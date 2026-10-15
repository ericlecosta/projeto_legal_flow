/**
 * Plugin de Babel para os testes: dentro de @Component({...}), troca `templateUrl: './x.html'`
 * por `template: '<conteúdo do arquivo>'` e remove `styleUrl`/`styleUrls`.
 * Assim o TestBed compila os componentes em modo JIT sem precisar buscar arquivos.
 */
const fs = require('node:fs');
const path = require('node:path');

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
    },
  };
};
