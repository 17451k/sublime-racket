# For development

## Installation

Clone the repository into the `Packages` directory, or symlink it there.
`Preferences > Browse Packages…` opens that directory; typical locations:

| OS      | Path                                                  |
|---------|-------------------------------------------------------|
| Linux   | `~/.config/sublime-text/Packages`                     |
| macOS   | `~/Library/Application Support/Sublime Text/Packages` |
| Windows | `%APPDATA%\Sublime Text\Packages`                     |

Sublime picks up edits to `Racket.sublime-syntax` on save. Open
`syntax_test_racket.rkt` and run Build (`Ctrl/Cmd+B`) to execute the syntax
tests.

## Regenerating the syntax files

`Racket.sublime-syntax` and `Scribble.sublime-syntax` are generated; never
edit them by hand. The hand-written part is `tools/syntax_template.yaml`;
the Scribble file is the same syntax with a prose top level. The three identifier lists (special
forms, builtin procedures, builtin values) are computed from the exports of
the `racket` module of the installed Racket:

```sh
racket tools/gen_syntax.rkt
```

Validate the result with:

```sh
python3 tools/check.py
```

## Scopes used

Scopes follow the standard Sublime naming (keyword.control, support.function,
variable.parameter, entity.name.function, ...), so any scheme works. Use
Tools > Developer > Show Scope Name to see the scope under the cursor.

| Construct | Scope |
|---|---|
| `;` line comment | `comment.line.semicolon.racket` |
| `#\| ... \|#` block comment | `comment.block.racket` |
| `#;` datum comment | `comment.block.sexp.racket` |
| `#lang` / `#reader` keyword | `keyword.control.lang.racket` |
| `#lang`/`#reader` target name | `variable.language.lang-name.racket` |
| `#ci` `#cs` `#CI` `#CS` | `comment.racket` |
| Strings | `string.quoted.double.racket` |
| Byte strings | `string.quoted.double.byte.racket` |
| Here strings | `string.unquoted.heredoc.racket` (opening tag: `constant.other.heredoc-tag.racket`) |
| Regex literals | `string.regexp.racket` |
| String/char escapes | `constant.character.escape.racket` |
| Characters | `constant.character.racket` |
| Booleans | `constant.language.boolean.racket` |
| Numbers | `constant.numeric.racket` |
| `#:keyword` | `constant.other.keyword.racket` |
| Quote/quasiquote/unquote markers | `keyword.operator.quote.racket` |
| Quoted symbol (`'foo`) | `constant.other.symbol.racket` |
| Parens/brackets/braces | `punctuation.section.{parens,brackets,braces}.{begin,end}.racket`; the list body is `meta.{parens,brackets,braces}.racket meta.sexp.racket` |
| Vector/hash/struct literal prefixes (`#(`, `#vu8(`, `#hash(`, `#s(`) | `keyword.other.literal-prefix.racket`; the `(` is `punctuation.definition.{vector,hash,struct}.begin.racket` |
| Special form (syntax export of `racket`), head or not | `keyword.control.racket` |
| Head operator `+ - * / = <= >= < >` | `keyword.operator.racket` (takes precedence over the builtin list) |
| Head `require` | `keyword.control.import.racket` |
| Head `provide` | `keyword.control.export.racket` |
| Head `define`/`define-values`/`define-syntax`/`define-syntax-rule` | `keyword.declaration.function.racket` |
| Head `define-for-syntax`, `define/contract`, `define/public`, `define/private`, `define/override`, `define/augment`, `define-inline`, `lambda`, `λ`, `define-syntaxes`, `define-values-for-*` | `keyword.control.racket` (but the following name/parameter list is still scoped as below) |
| Head `struct`/`define-struct` | `keyword.declaration.struct.racket` |
| Head builtin procedure | `support.function.builtin.racket` |
| Head, otherwise (paren/brace list) | `variable.function.racket` |
| Head, otherwise (bracket list) | `variable.parameter.racket` |
| Function/binding name after `define`-family | `entity.name.function.racket` |
| Parameter names (lambda/define params, `let` bracket bindings) | `variable.parameter.racket` |
| Struct name | `entity.name.type.struct.racket` |
| Struct field names | `variable.other.member.racket` |
| Non-head builtin variable | `support.variable.builtin.racket` |
| Non-head builtin procedure | `support.function.builtin.racket` |
| Operators `+ - * / = <= >= < >` | `keyword.operator.racket` |
| Lone `.` | `keyword.operator.dot.racket` |
| Any other symbol | `variable.other.racket` |
| Piped symbol `\|...\|` | `variable.other.racket` (delimiters: `punctuation.definition.symbol.racket`) |
| Comment and string delimiters | `punctuation.definition.comment[.begin/.end].racket`, `punctuation.definition.string.{begin,end}.racket` |
| `@`-expression opener | `punctuation.definition.at-expression.racket` |
| `@cmd` symbol part | `variable.function.at-expression.racket` |
| `@cmd\|...\|` piped cmd delimiters | `punctuation.definition.at-cmd.racket` |
| `@cmd{...}` / `@cmd\|...{...}...\|` braces | `punctuation.section.braces.{begin,end}.at-expression.racket` |
| `@`-expression text body | `meta.at-body.racket` |
| `@;{ ... }` block comment | `comment.block.at-expression.racket` (delimiters: `punctuation.definition.comment.racket`) |
| `@; ...` line comment | `comment.line.at-expression.racket` (delimiter: `punctuation.definition.comment.racket`) |

## Known limitations

Sublime's syntax engine is a regex/context-stack matcher, not a parser, so
some constructs are approximated:

- **Head-of-list detection is lexical.** The first datum after `(`, `[` or
  `{` is treated as the operator position. A quoted list such as `'(a b)`
  therefore scopes `a` as a function call;
  numbers, strings and `#…` literals in that position are recognised and
  left alone.
- **`define` / `lambda` parameter lists are recursive contexts, not an AST.**
  `(define (f a b) …)`, curried `(define ((f a) b) …)`, and `(lambda (x y) …)`
  are handled; unusual nesting inside a parameter list (for example a
  default value that itself contains a lambda) may scope some symbols as
  parameters that are not.
- **`[x 1]` binding heads are scoped as parameters** regardless of whether
  the enclosing form is `let`, `cond`, `match`, or anything else, so `cond`
  clause tests that start with a symbol also appear as parameters.
- **`#;` datum comments skip exactly one datum by bracket counting**, with
  quote prefixes and strings understood. A datum whose first character is
  `#` followed by a bracket (`#;#(1 2)`) is only partially commented.
- **Number literals cover common forms only**: integers, decimals,
  exponents, rationals, simple complex numbers, `#x`/`#b`/`#o`/`#e`/`#i`
  prefixes and `±inf.0`/`±nan.0`. Exotic forms such as `1.` or extflonums
  fall through to symbol scoping.
- **Scopes are context-free.** Shadowing a builtin (`(define (map …) …)`)
  still highlights later uses of `map` as a builtin.
- **`@cmd|<punct>{...}<punct>|` alternative delimiters are matched loosely.**
  The closing punctuation run is matched as "some run of punctuation
  characters", not verified to be the exact reverse of the opening run, and
  likewise for the nested `|<punct>@` escape inside the body. A regex/
  context-stack matcher cannot backreference a reversed capture group, so a
  mismatched closer (`@foo|<<{ ... }>|`) is still accepted.
- **`@` is an at-expression opener anywhere in `.rkt` files**, even without
  `#lang at-exp racket`. A bare symbol that happens to start with `@` at the
  start of a token (rather than appearing mid-symbol, e.g. `a@b`) is
  misread as an at-expression opener.

## Possible future syntax additions

- Scoping `[x 1]` heads as bindings only inside `let`-family, `for`-family
  and `match` forms, and as ordinary expressions elsewhere (for example
  `cond` clauses).
- Highlighting for `#lang`s other than `racket` with different export sets
  (`typed/racket`, `racket/base`), selected by the `#lang` line.
- Completions for builtin identifiers, derived from the same generated
  lists.
