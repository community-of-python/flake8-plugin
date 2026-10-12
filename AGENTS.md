# Import analysis

Import checks must inspect AST and filesystem data without executing inspected
packages, import hooks, extension modules, or `.pth` files. Do not use runtime
imports or `find_spec` to resolve application dependencies. Leave unresolved or
dynamic imports unchecked rather than guessing their type.

COP001 must remain off by default. Repositories opt in explicitly through
Flake8's `extend-select = ["COP001"]` setting. Keep one COP extension.
