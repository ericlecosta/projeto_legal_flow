/**
 * Babel só é usado pelo Jest (o build do Angular usa o próprio compilador).
 * - preset-typescript remove os tipos; preset-env gera código para a versão do Node em uso;
 * - decorators "legacy" = experimentalDecorators do tsconfig (@Component, @Injectable, @Pipe);
 * - no ambiente de teste, inline-angular-resources troca templateUrl pelo HTML do componente (JIT).
 */
module.exports = (api) => {
  const isTest = api.env('test');
  return {
    presets: [
      ['@babel/preset-env', { targets: { node: 'current' } }],
      ['@babel/preset-typescript', { allowDeclareFields: true }],
    ],
    plugins: [
      ['@babel/plugin-proposal-decorators', { version: 'legacy' }],
      ...(isTest ? ['./jest/inline-angular-resources.js'] : []),
    ],
  };
};
