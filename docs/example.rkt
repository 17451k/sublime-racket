#lang racket

;; Line comment, and a block comment: #| nested #| inside |# |#
(require racket/list)
(provide (struct-out point) distance)

(struct point (x y) #:transparent)

(define (distance p q)
  (sqrt (+ (sqr (- (point-x p) (point-x q)))
           (sqr (- (point-y p) (point-y q))))))

(define origin (point 0 0))

(define (describe pt #:precision [digits 2])
  (let ([d (distance origin pt)]
        [tag 'polar])
    (format "~a: ~a" tag (real->decimal-string d digits))))

(for/list ([n (in-range 5)] #:when (odd? n))
  #;(this datum is commented out)
  (map add1 (list n #xff 1/2 +inf.0 #\λ #t)))

(match (regexp-match #px"(\\d+)-(\\d+)" "12-34")
  [(list _ a b) `(,a ,@(list b))]
  [#f "no match"])
