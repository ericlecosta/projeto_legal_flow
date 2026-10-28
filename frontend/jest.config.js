/** Jest com Babel (sem ts-jest): veja babel.config.js. */
module.exports = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  testMatch: ['**/*.spec.ts'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleFileExtensions: ['ts', 'js', 'mjs', 'json'],
  transform: {
    '^.+\\.(ts|js|mjs)$': '<rootDir>/jest/babel-transformer.js',
  },
  // Os pacotes do Angular e o rxjs são publicados como ESM: precisam passar pelo Babel também.
  transformIgnorePatterns: ['/node_modules/(?!(@angular|rxjs)/)'],
  collectCoverageFrom: ['src/app/**/*.ts', '!src/app/**/*.spec.ts', '!src/app/**/*.routes.ts'],
};
