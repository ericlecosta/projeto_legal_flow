/**
 * Plugin de Babel para os testes (o Angular compila os componentes em JIT dentro do Jest):
 *
 * 1. Dentro de @Component({...}), troca `templateUrl: './x.html'` por `template: '<conteúdo>'`
 *    e remove `styleUrl`/`styleUrls`, para o TestBed não precisar buscar arquivos.
 * 2. Em classes com @Component/@Directive, gera os metadados das APIs de signal
 *    (input, input.required, output, viewChild, viewChildren, contentChild, contentChildren)
 *    no formato `static propDecorators`, que o JIT do Angular lê. No build normal quem faz isso
 *    é o compilador do Angular; sem estes metadados um `input.required()` nunca recebe valor.
 */
const fs = require('node:fs');
const path = require('node:path');
const { addNamed } = require('@babel/helper-module-imports');

const QUERIES = {
  viewChild: { decorator: 'ViewChild', first: true },
  viewChildren: { decorator: 'ViewChildren', first: false },
  contentChild: { decorator: 'ContentChild', first: true },
  contentChildren: { decorator: 'ContentChildren', first: false },
};

/** `input(...)`, `input.required(...)`, `viewChild(...)` → { fn: 'input', required: true }. */
function signalCall(t, node) {
  if (!t.isCallExpression(node)) return null;
  const { callee } = node;
  if (t.isIdentifier(callee)) return { fn: callee.name, required: false };
  if (
    t.isMemberExpression(callee) &&
    t.isIdentifier(callee.object) &&
    t.isIdentifier(callee.property, { name: 'required' })
  ) {
    return { fn: callee.object.name, required: true };
  }
  return null;
}

/** Valor literal de `alias` em `{ alias: 'x' }`, se houver. */
function aliasFrom(t, options) {
  if (!t.isObjectExpression(options)) return null;
  const alias = options.properties.find(
    (p) =>
      t.isObjectProperty(p) &&
      t.isIdentifier(p.key, { name: 'alias' }) &&
      t.isStringLiteral(p.value),
  );
  return alias ? alias.value.value : null;
}

function isAngularClass(t, classNode) {
  return (classNode.decorators || []).some(
    (d) =>
      t.isCallExpression(d.expression) &&
      t.isIdentifier(d.expression.callee) &&
      ['Component', 'Directive'].includes(d.expression.callee.name),
  );
}

module.exports = function inlineAngularResources({ types: t }) {
  return {
    name: 'inline-angular-resources',
    visitor: {
      CallExpression(callPath, state) {
        if (!t.isIdentifier(callPath.node.callee, { name: 'Component' })) return;
        const [config] = callPath.node.arguments;
        if (!t.isObjectExpression(config)) return;

        const dir = path.dirname(state.file.opts.filename);
        config.properties = config.properties.flatMap((prop) => {
          if (!t.isObjectProperty(prop) || !t.isIdentifier(prop.key)) return [prop];
          if (prop.key.name === 'templateUrl' && t.isStringLiteral(prop.value)) {
            const html = fs.readFileSync(path.resolve(dir, prop.value.value), 'utf8');
            return [t.objectProperty(t.identifier('template'), t.stringLiteral(html))];
          }
          if (prop.key.name === 'styleUrl' || prop.key.name === 'styleUrls') return [];
          return [prop];
        });
      },

      Class(classPath) {
        if (!isAngularClass(t, classPath.node)) return;
        const imports = {};
        const ref = (name) => {
          imports[name] ??= addNamed(classPath, name, '@angular/core', { nameHint: `jit${name}` });
          return t.cloneNode(imports[name]);
        };

        const entries = [];
        for (const member of classPath.node.body.body) {
          if (!t.isClassProperty(member) || member.static || !t.isIdentifier(member.key)) continue;
          const call = signalCall(t, member.value);
          if (!call) continue;
          const field = member.key.name;
          const args = member.value.arguments;
          let decorator = null;

          if (call.fn === 'input') {
            const alias = aliasFrom(t, call.required ? args[0] : args[1]) ?? field;
            decorator = {
              type: ref('Input'),
              args: [
                t.objectExpression([
                  t.objectProperty(t.identifier('isSignal'), t.booleanLiteral(true)),
                  t.objectProperty(t.identifier('alias'), t.stringLiteral(alias)),
                  t.objectProperty(t.identifier('required'), t.booleanLiteral(call.required)),
                  t.objectProperty(t.identifier('transform'), t.identifier('undefined')),
                ]),
              ],
            };
          } else if (call.fn === 'output') {
            decorator = {
              type: ref('Output'),
              args: [t.stringLiteral(aliasFrom(t, args[0]) ?? field)],
            };
          } else if (QUERIES[call.fn]) {
            const [predicate, options] = args;
            const opts = t.isObjectExpression(options)
              ? options.properties.map((p) => t.cloneNode(p))
              : [];
            opts.push(t.objectProperty(t.identifier('isSignal'), t.booleanLiteral(true)));
            decorator = {
              type: ref(QUERIES[call.fn].decorator),
              args: [t.cloneNode(predicate), t.objectExpression(opts)],
            };
          }

          if (decorator) {
            entries.push(
              t.objectProperty(
                t.identifier(field),
                t.arrayExpression([
                  t.objectExpression([
                    t.objectProperty(t.identifier('type'), decorator.type),
                    t.objectProperty(t.identifier('args'), t.arrayExpression(decorator.args)),
                  ]),
                ]),
              ),
            );
          }
        }

        if (entries.length) {
          classPath.node.body.body.push(
            t.classProperty(
              t.identifier('propDecorators'),
              t.objectExpression(entries),
              null,
              null,
              false,
              true,
            ),
          );
        }
      },
    },
  };
};
