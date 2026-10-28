/**
 * babel-jest com o HTML dos componentes na chave de cache.
 *
 * O plugin inline-angular-resources embute o templateUrl no código transformado. O cache do Jest
 * só olha o .ts, então mudar apenas o .html deixava os testes rodando com o template antigo.
 */
const fs = require('node:fs');
const path = require('node:path');
const babelJest = require('babel-jest').default;

const transformer = babelJest.createTransformer();
const TEMPLATE_URL = /templateUrl\s*:\s*['"`]([^'"`]+)['"`]/g;

function templates(source, filename) {
  const dir = path.dirname(filename);
  let content = '';
  for (const [, url] of source.matchAll(TEMPLATE_URL)) {
    try {
      content += fs.readFileSync(path.resolve(dir, url), 'utf8');
    } catch {
      // Template inexistente: o próprio plugin acusa o erro na transformação
    }
  }
  return content;
}

module.exports = {
  ...transformer,
  getCacheKey(source, filename, options) {
    return transformer.getCacheKey(source + templates(source, filename), filename, options);
  },
  getCacheKeyAsync(source, filename, options) {
    return transformer.getCacheKeyAsync(source + templates(source, filename), filename, options);
  },
};
