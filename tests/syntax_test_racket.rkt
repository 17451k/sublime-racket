; SYNTAX TEST "Racket.sublime-syntax"

#lang racket
;^^^^ keyword.control.lang.racket
;     ^^^^^^ variable.language.lang-name.racket

; this is a line comment
; <- punctuation.definition.comment.racket
;^^^^^^^^^^^^^^^^^^^^^^^ comment.line.semicolon.racket

#| a block comment |#
;^ punctuation.definition.comment.begin.racket
;^^^^^^^^^^^^^^^^^^^^ comment.block.racket

#| outer #| inner |# still-outer |#
;^ punctuation.definition.comment.begin.racket
;        ^^ punctuation.definition.comment.begin.racket

#;(a (b) c)
;^ punctuation.definition.comment.racket
; ^^^^^^^^^ comment.block.sexp.racket

#; foo
;^ punctuation.definition.comment.racket
;  ^^^ comment.block.sexp.racket

"a string with \n escape"
; <- punctuation.definition.string.begin.racket
;^^^^^^^^^^^^^^^^^^^^^^^^ string.quoted.double.racket
;              ^^ constant.character.escape.racket

#"a byte string"
;^ punctuation.definition.string.begin.racket
;^^^^^^^^^^^^^^^ string.quoted.double.byte.racket

#rx"a[bc]+"
;^^^ punctuation.definition.string.begin.racket
;^^^^^^^^^^ string.regexp.racket

#\space
;^^^^^^ constant.character.racket

#\x41
;^^^^ constant.character.racket

#\(
;^^ constant.character.racket

#t
;^ constant.language.boolean.racket

#false
;^^^^^ constant.language.boolean.racket

42
;^ constant.numeric.racket

3.14
;^^^ constant.numeric.racket

1/2
;^^ constant.numeric.racket

1e10
;^^^ constant.numeric.racket

#x1A
;^^^ constant.numeric.racket

+inf.0
;^^^^^ constant.numeric.racket

#:key
;^^^^ constant.other.keyword.racket

'foo
; <- keyword.operator.quote.racket
;^^^ constant.other.symbol.racket

'(a b c)
; <- keyword.operator.quote.racket
;^ punctuation.section.parens.begin.racket

(define (add-one x) (+ x 1))
; <- punctuation.section.parens.begin.racket
;^^^^^^ keyword.declaration.function.racket
;       ^ punctuation.section.parens.begin.racket
;        ^^^^^^^ entity.name.function.racket
;                ^ variable.parameter.racket

(lambda (x y) (+ x y))
;^^^^^^ keyword.control.racket
;       ^ punctuation.section.parens.begin.racket
;        ^ variable.parameter.racket
;          ^ variable.parameter.racket

(let ([x 1] [y 2]) (+ x y))
;^^^ keyword.control.racket
; <- punctuation.section.parens.begin.racket
;     ^ punctuation.section.brackets.begin.racket
;      ^ variable.parameter.racket

(struct point (x y))
;^^^^^^ keyword.declaration.struct.racket
;       ^^^^^ entity.name.type.struct.racket
;             ^ punctuation.section.parens.begin.racket
;              ^ variable.other.member.racket

(require racket/list)
;^^^^^^^ keyword.control.import.racket

(provide add-one)
;^^^^^^^ keyword.control.export.racket

(map add1 '(1 2 3))
;^^^ support.function.builtin.racket

(displayln (map add1 (list 1 2 3)))
;                     ^^^^ support.function.builtin.racket

null
;^^^ support.variable.builtin.racket

pi
;^ support.variable.builtin.racket

(+ 1 2)
;^ keyword.operator.racket

(some-user-function 1 2)
;^^^^^^^^^^^^^^^^^^ variable.function.racket

#(1 2 3)
; <- keyword.other.literal-prefix.racket
;^ punctuation.definition.vector.begin.racket

#hash((a . 1))
;^^^^ keyword.other.literal-prefix.racket
;    ^ punctuation.definition.hash.begin.racket

|foo bar|
; <- punctuation.definition.symbol.racket
;^^^^^^^ variable.other.racket

#<<HERE
;^^ punctuation.definition.string.begin.racket
;  ^^^^ constant.other.heredoc-tag.racket
inside the here string
HERE
;^^^ string.unquoted.heredoc.racket

(define (f a b) (+ a b))
(g 1)
;^ variable.function.racket
;  ^ constant.numeric.racket

(let ([x 1]) x)
;      ^ variable.parameter.racket

(define (outer) (define (inner y) y) (inner 1))
;        ^^^^^ entity.name.function.racket
;                        ^^^^^ entity.name.function.racket
;                              ^ variable.parameter.racket

(map add1 '(1 2 3))
;^^^ support.function.builtin.racket
;           ^ constant.numeric.racket
;             ^ constant.numeric.racket
("str" 1)
;^^^ string.quoted.double.racket
(#t 1)
;^ constant.language.boolean.racket

@foo{hello world}
; <- punctuation.definition.at-expression.racket
;^^^ variable.function.at-expression.racket
;   ^ punctuation.section.braces.begin.at-expression.racket
;    ^^^^^ meta.at-body.racket
;               ^ punctuation.section.braces.end.at-expression.racket

@map[add1 '(1 2)]
;^^^ support.function.builtin.racket
;    ^^^^ support.function.builtin.racket
;             ^ constant.numeric.racket

@section[#:tag "x"]{Title @emph{here} done}
;        ^^^^^ constant.other.keyword.racket
;               ^ string.quoted.double.racket
;                          ^^^^ variable.function.at-expression.racket
;                               ^^^^ meta.at-body.racket meta.at-body.racket

@foo{a {b} c}
;       ^ meta.at-body.racket
;          ^ meta.at-body.racket

@;{ block comment }
;   ^^^^^ comment.block.at-expression.racket

@; line comment
;  ^^^^ comment.line.at-expression.racket

@"str"
; ^^^ string.quoted.double.racket

@(+ 1 2)
; ^ keyword.operator.racket
;   ^ constant.numeric.racket

@foo|{ bar }|
;      ^^^ meta.at-body.racket

@foo|<<{ x |<<@baz{y} }>>|
;              ^^^ variable.function.at-expression.racket

(list a@b c)
;     ^^^ variable.other.racket
