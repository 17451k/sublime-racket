#lang racket
(define (f x)
  (let loop ([i 0]
             [acc (list 1 2 3)])
    (if (> i 10)
        (reverse acc)
        (loop
         (add1 i)
         (cons (compute-something i x)
               acc)))))
((make-thing argument-one)
 argument-number-two
 argument-number-three)
'(alpha beta
        gamma
        delta
        epsilon
        zeta
        eta
        theta)
(define lst
  '(1 2
      3
      4
      5
      6
      7
      8
      9
      10
      11
      12
      13
      14
      15))
(cond
  [(> x 1)
   (displayln "a")
   (displayln "b")]
  [else (displayln "ccccccccccc")])
(my-unknown-macro (some arg)
                  (body-one argument)
                  (body-two argument))
(with-handlers ([exn:fail?
                 (lambda (e)
                   (displayln
                    "failed here")
                   1)])
  (do-something-long 1 2 3))
(for/fold ([acc 0]
           [other-acc 1])
          ([x (in-list xs)]
           [y (in-list ys)])
  (values (+ acc x) y))
(struct point (x y)
  #:transparent
  #:mutable
  #:property prop:foo
  12)
(define/contract (g a b)
  (-> integer? integer? integer?)
  (+ a b))
(send obj method
      argument-one
      argument-two
      argument-three)
(match v
  [(list a b)
   (displayln a)
   (+ a b)]
  [_ 0])
(class object%
  (init-field x y)
  (super-new)
  (define/public (get) x))
(when (some-condition? x)
  (do-this thing)
  (do-that thing))
(hash 'a
      1
      'b
      2
      'cccccccccc
      3
      'ddddddddddd
      4)
#(vector-elem-one
  vector-elem-two
  vector-elem-three)
(f #:keyword-one value-one
   #:keyword-two value-two
   positional)
(let-values ([(a b) (values 1 2)]
             [(c) (values 3)])
  (list a b c))
(lambda (x y)
  (displayln x)
  (displayln y))
(module+ test
  (require rackunit)
  (check-equal? (f 1) 2))
(if (some-test-here x)
    (then-branch-expression x)
    (else-branch-expression x))
(syntax-case stx ()
  [(_ a b) #'(list a b)]
  [(_ a) #'(list a)])
(begin
  (one-expr argument)
  (two-expr argument))
(parameterize ([current-output-port
                (open-output-string)])
  (displayln "x")
  (displayln "y"))
;; extras
(define (g lst)
  ; a comment inside a body
  (for ([x (in-list lst)]
        #:when (odd? x))
    (displayln x)
    (displayln (* x x x x x x x x))))
(let* ([first-binding (compute 1)]
       [second-binding
        (compute first-binding)])
  (+ first-binding second-binding))
(case (classify value)
  [(small tiny) (handle-small value)]
  [(large) (handle-large value)]
  [else #f])
(define-values (quotient-part
                remainder-part)
  (quotient/remainder numerator
                      denominator))
(begin0 (compute-the-result argument)
  (cleanup-afterwards argument))
(define-syntax-rule (swap! a b)
  (let ([tmp a])
    (set! a b)
    (set! b tmp)))
(require racket/list
         racket/string
         racket/match
         racket/format)
(unless (valid? input)
  (raise-argument-error 'f
                        "valid?"
                        input))
(define ht
  (make-hash (list (cons 'alpha 1)
                   (cons 'beta 2)
                   (cons 'gamma 3))))
(letrec ([even? (lambda (n)
                  (or (zero? n)
                      (odd? (sub1 n))))]
         [odd? (lambda (n)
                 (and (not (zero? n))
                      (even?
                       (sub1 n))))])
  (even? 10))
(string-append "first string here"
               "second string here"
               "third one")
(module helper racket/base
  (provide help)
  (define (help)
    'helped))
(case-lambda
  [(a) (list a)]
  [(a b) (list a b)]
  [(a b . rest) (list* a b rest)])
(syntax-parse stx
  [(_ name:id value:expr)
   #'(define name value)]
  [(_ name:id) #'(define name #f)])
(define (h #:keyword-argument
           [keyword-argument 10]
           . rest-arguments)
  (apply +
         keyword-argument
         rest-arguments))
(λ (x)
  (displayln
   "a long string to break the line")
  x)
(test-case "addition works"
  (check-equal? (+ 1 1) 2)
  (check-equal? (+ 2 2) 4))
(struct point-with-long-name
        (field-one field-two
                   field-three)
  #:transparent)
(struct point-with-long-name
        parent-struct
        (field-one field-two
                   field-three)
  #:transparent)
(for/vector #:length 10
            ([i (in-range 10)]
             [j (in-range 10)])
  (compute-something i j))
