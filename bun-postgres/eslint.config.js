import stylistic from "@stylistic/eslint-plugin";
import tsParser from "@typescript-eslint/parser";

// Include exported declarations and functions assigned to variables.
const functions = {
  selector: [
    "FunctionDeclaration",
    "ExportNamedDeclaration[declaration.type='FunctionDeclaration']",
    "ExportDefaultDeclaration[declaration.type='FunctionDeclaration']",
    "VariableDeclaration[declarations.0.init.type=/^(ArrowFunctionExpression|FunctionExpression)$/]",
    "ExportNamedDeclaration[declaration.declarations.0.init.type=/^(ArrowFunctionExpression|FunctionExpression)$/]",
  ].join(", "),
};

export default [
  {
    ignores: [
      "node_modules/**",
      ".vercel/**",
      "public/vendor/**",
      "src/assets.ts",
    ],
  },
  {
    files: ["**/*.{js,ts,tsx}"],
    languageOptions: { parser: tsParser },
    plugins: { "@stylistic": stylistic },
    rules: {
      "@stylistic/padding-line-between-statements": [
        "error",
        { blankLine: "always", prev: "*", next: functions },
        { blankLine: "always", prev: functions, next: "*" },
      ],
      "@stylistic/no-multiple-empty-lines": [
        "error",
        { max: 1, maxBOF: 0, maxEOF: 0 },
      ],
    },
  },
];
