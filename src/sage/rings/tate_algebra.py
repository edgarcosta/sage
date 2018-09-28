from sage.structure.factory import UniqueFactory
from sage.monoids.monoid import Monoid_class
from sage.rings.ring import CommutativeAlgebra
from sage.rings.integer_ring import ZZ
from sage.rings.rational_field import QQ
from sage.rings.padics.padic_generic import pAdicGeneric

from sage.categories.monoids import Monoids
from sage.categories.commutative_algebras import CommutativeAlgebras
from sage.categories.complete_discrete_valuation import CompleteDiscreteValuationRings
from sage.categories.complete_discrete_valuation import CompleteDiscreteValuationFields
from sage.categories.pushout import pushout

from sage.structure.category_object import normalize_names
from sage.rings.polynomial.polynomial_ring_constructor import PolynomialRing
from sage.rings.polynomial.term_order import TermOrder
from sage.rings.tate_algebra_element import TateAlgebraTerm
from sage.rings.tate_algebra_element import TateAlgebraElement

from sage.rings.polynomial.polydict import ETuple


# Factory
#########

class TateAlgebraFactory(UniqueFactory):
    r"""
    Construct a Tate algebra over a `p`-adic field.

    Given a `p`-adic field `K`, variables `X_1,\dots,X_k`
    and convergence log radii `v_1, \dots, v_n` in `\RR`, the corresponding
    Tate algebra `K{X_1,\dots,X_k}` consists of power series witj
    coefficients `a_{i_1,\dots,i_n}` in `K` such that

    .. MATH::

        `\text{val}(a_{i_1,\dots,i_n}) - (i_1 v_1 + \cdots + i_n v_n)`

    tends to infinity as `i_1,\dots,i_n` go towards infinity.

    INPUT:

    - ``base`` -- a `p`-adic ring or field; if a ring is given, the
      Tate algebra over its fraction field will be constructed

    - ``prec`` -- an integer or ``None`` (default: ``None``), the 
      precision cap; it is used if an exact object must be truncated
      in order to do an arithmetic operation. 
      If left as ``None``, it will be set to the precision cap of 
      the base field.

    - ``log_radii`` -- an integer or a list or a tuple of integers 
      (default: ``0``), the value(s) `v_i`.
      If an integer is given, this will be the common value for all
      `v_i`.

    - ``names`` -- names of the indeterminates

    - ``order`` - (default: ``degrevlex``) the monomial ordering 
      used to break ties when comparing terms with the same 
      coefficient valuation

    EXAMPLES::

        sage: R = Zp(2, 10, print_mode='digits'); R
        2-adic Ring with capped relative precision 10
        sage: A.<x,y> = TateAlgebra(R, order='lex'); A
        Tate Algebra in x (val >= 0), y (val >= 0) over 2-adic Field with capped relative precision 10

    We observe that the result is the Tate algebra over the fraction
    field of `R` and not `R` itself::

        sage: A.base_ring()
        2-adic Field with capped relative precision 10
        sage: A.base_ring() is R.fraction_field()
        True

    If we want to construct the ring of integers of the Tate algebra,
    we must use the method :meth:`integer_ring`::

        sage: AA = A.integer_ring(); AA
        Integer ring of the Tate Algebra in x (val >= 0), y (val >= 0) over 2-adic Field with capped relative precision 10
        sage: AA.base_ring()
        2-adic Ring with capped relative precision 10
        sage: AA.base_ring() is R
        True

    The term ordering is used (in particular) to determine how series are 
    displayed. Terms are compared first according to the valuation of their 
    coefficient, and ties are broken using the monomial ordering::

        sage: A.term_order()
        Lexicographic term order
        sage: f = 2 + y^5 + x^2; f
        (...0000000001)*x^2 + (...0000000001)*y^5 + (...00000000010)
        sage: B.<x,y> = TateAlgebra(R); B
        Tate Algebra in x (val >= 0), y (val >= 0) over 2-adic Field with capped relative precision 10
        sage: B.term_order()
        Degree reverse lexicographic term order
        sage: B(f)
        (...0000000001)*y^5 + (...0000000001)*x^2 + (...00000000010)

    Here are examples of Tate algebra with smaller radii of convergence::

        sage: B.<x,y> = TateAlgebra(R, log_radii=-1); B
        Tate Algebra in x (val >= 1), y (val >= 1) over 2-adic Field with capped relative precision 10
        sage: C.<x,y> = TateAlgebra(R, log_radii=[-1,-2]); C
        Tate Algebra in x (val >= 1), y (val >= 2) over 2-adic Field with capped relative precision 10

    """
    def create_key(self, base, prec=None, log_radii=ZZ(0), names=None, order='degrevlex'):
        if not isinstance(base, pAdicGeneric):
            raise TypeError("The base ring must be a p-adic field")
        # TODO: allow for arbitrary CDVF
        base = base.fraction_field()
        if names is None:
            raise ValueError("You must specify the names of the variables")
        names = normalize_names(-1, names)
        ngens = len(names)
        if not isinstance(log_radii, (list, tuple)):
            log_radii = [ZZ(log_radii)] * ngens
        elif len(log_radii) != ngens:
            raise ValueError("The number of radii does not match the number of variables")
        else:
            log_radii = [ ZZ(r) for r in log_radii ]
        order = TermOrder(order, ngens)
        if prec is None:
            prec = base.precision_cap()
        key = (base, prec, tuple(log_radii), names, order)
        return key

    def create_object(self, version, key):
        (base, prec, log_radii, names, order) = key
        return TateAlgebra_generic(base, prec, log_radii, names, order)

TateAlgebra = TateAlgebraFactory("TateAlgebra")


# Parent for terms
##################

class TateTermMonoid(Monoid_class):
    r"""
    A base class for Tate algebra terms
    
    A term in a Tate algebra `K\{X_1,\dots,X_n\}` (resp. in its ring of
    integers) is a monomial in this ring.
    
    Those terms form a pre-ordered monoid, with term multiplication and the
    term order of the parent Tate algebra.
    
    """
    
    def __init__(self, A):
        r"""
        Initialize the Tate term monoid

        INPUT:
    
        - ``A`` -- a Tate algebra
    
        EXAMPLES::
    
            sage: R = pAdicRing(2, 10)
            sage: A.<x,y> = TateAlgebra(R, log_radii=1)
            sage: T = A.monoid_of_terms(); T
            Monoid of terms in x (val >= -1), y (val >= -1) over 2-adic Field with capped relative precision 10

        TESTS::

            sage: A.<x,y> = TateAlgebra(Zp(2), log_radii=1)
            sage: T = A.monoid_of_terms()
            sage: #TestSuite(T).run()
        
        """
        # This function is not exposed to the user
        # so we do not check the inputs
        self.element_class = TateAlgebraTerm
        names = A.variable_names()
        Monoid_class.__init__(self, names)
        self._base = A.base_ring()
        self._field = A._field
        self._names = names
        self._ngens = len(self._names)
        self._log_radii = ETuple(A.log_radii())
        self._order = A.term_order()
        self._parent_algebra = A

    def _repr_(self):
        r"""
        Return a string representation of this Tate term monoid

        EXAMPLES::

            sage: R = pAdicRing(2, 10)
            sage: A.<x,y> = TateAlgebra(R, log_radii=[1,1], order="lex")
            sage: A.monoid_of_terms()  # indirect doctest
            Monoid of terms in x (val >= -1), y (val >= -1) over 2-adic Field with capped relative precision 10

        """
        if self._ngens == 0:
            return "Monoid of terms over %s" % self._base
        vars = ""
        for i in range(self._ngens):
            vars += ", %s (val >= %s)" % (self._names[i], -self._log_radii[i])
        return "Monoid of terms in %s over %s" % (vars[2:], self._base)

    def _coerce_map_from_(self, R):
        r"""
        Return ``True`` if ``R`` coerces to this monoid.

        EXAMPLES::

            sage: R = Zp(2, 10, print_mode='digits')
            sage: A.<x,y> = TateAlgebra(R)
            sage: T = A.monoid_of_terms()

        A ring coerces into a monoid of terms if and only if 
        it coerces into its base ring::

            sage: T.has_coerce_map_from(ZZ)  # indirect doctest
            True
            sage: T.has_coerce_map_from(GF(2))  # indirect doctest
            False

        ::
        
            sage: S.<a> = Zq(4)
            sage: B.<x,y> = TateAlgebra(S)
            sage: U = B.monoid_of_terms()
            sage: U.has_coerce_map_from(T)  # indirect doctest
            True
            sage: T.has_coerce_map_from(U)  # indirect doctest
            False

        Note that a Tate algebra does not coerce into a monoid of terms::

            sage: U.has_coerce_map_from(A) # indirect doctest
            False
            sage: T.has_coerce_map_from(B) # indirect doctest
            False

        Variable names must match exactly::
        
            sage: B.<x,z> = TateAlgebra(R)
            sage: U = B.monoid_of_terms()
            sage: T.has_coerce_map_from(U) # indirect doctest
            False
            sage: U.has_coerce_map_from(T) # indirect doctest
            False

        and appears in the same order:
        
            sage: B.<y,x> = TateAlgebra(R); B
            Tate Algebra in y (val >= 0), x (val >= 0) over 2-adic Field with capped relative precision 10
            sage: U = B.monoid_of_terms()
            sage: T.has_coerce_map_from(U) # indirect doctest
            False
            sage: U.has_coerce_map_from(T) # indirect doctest
            False

        Term orders must also match::
        
            sage: B.<x,y> = TateAlgebra(R, order="lex")
            sage: U = B.monoid_of_terms()
            sage: T.has_coerce_map_from(U) # indirect doctest
            False
            sage: U.has_coerce_map_from(T) # indirect doctest
            False

        """
        base = self._base
        if base.has_coerce_map_from(R):
            return True
        if isinstance(R, TateTermMonoid):
            return self._parent_algebra.has_coerce_map_from(R.algebra_of_series())
        if isinstance(R, TateAlgebraElement):
            return self._parent_algebra.has_coerce_map_from(R)

    def algebra_of_series(self):
        r"""
        Return the Tate algebra corresponding to this Tate term monoid.

        EXAMPLES::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: T = A.monoid_of_terms()
            sage: T.algebra_of_series()
            Tate Algebra in x (val >= 0), y (val >= 0) over 2-adic Field with capped relative precision 10
            sage: T.algebra_of_series() is A
            True
        
        """
        return self._parent_algebra    
            
    def base_ring(self):
        r"""
        Return the base ring of this Tate term monoid.

        EXAMPLES::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: T = A.monoid_of_terms()
            sage: T.base_ring()
            2-adic Field with capped relative precision 10

        We observe that the base field is not ``R`` but its
        fraction field::

            sage: T.base_ring() is R
            False
            sage: T.base_ring() is R.fraction_field()
            True

        If we really want to create an integral Tate algebra,
        we have to invoke the method :meth:`integer_ring`::

            sage: AA = A.integer_ring(); AA
            Integer ring of the Tate Algebra in x (val >= 0), y (val >= 0) over 2-adic Field with capped relative precision 10
            sage: AA.base_ring()
            2-adic Ring with capped relative precision 10
            sage: AA.base_ring() is R
            True

        """
        return self._base

    def variable_names(self):
        r"""
        Return the names of the variables of this Tate term monoid.

        EXAMPLES::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: T = A.monoid_of_terms()
            sage: T.variable_names()
            ('x', 'y')

        """
        return self._names

    def log_radii(self):
        r"""
        Return the log radii of convergence of this Tate term monoid.

        EXAMPLES::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: T = A.monoid_of_terms()
            sage: T.log_radii()
            (0, 0)

            sage: B.<x,y> = TateAlgebra(R, log_radii=[1,2])
            sage: B.monoid_of_terms().log_radii()
            (1, 2)

        """
        return tuple(self._log_radii)

    def term_order(self):
        r"""
        Return the term order on this Tate term monoid.

        EXAMPLES::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: T = A.monoid_of_terms()
            sage: T.term_order()  # default term order is grevlex
            Degree reverse lexicographic term order

            sage: A.<x,y> = TateAlgebra(R, order='lex')
            sage: T = A.monoid_of_terms()
            sage: T.term_order()
            Lexicographic term order

        """
        return self._order

    def ngens(self):
        r"""
        Return the number of variables in the Tate term monoid

        EXAMPLES::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: T = A.monoid_of_terms()
            sage: T.ngens()
            2

        """
        return self._ngens



# Tate algebras
###############

class TateAlgebra_generic(CommutativeAlgebra):
    def __init__(self, field, prec, log_radii, names, order, integral=False):
        """
        Initialize the Tate algebra

        TESTS::

            sage: A.<x,y> = TateAlgebra(Zp(2), log_radii=1)
            sage: #TestSuite(A).run()

        """
        self.element_class = TateAlgebraElement
        self._field = field
        self._cap = prec
        self._log_radii = ETuple(log_radii)  # TODO: allow log_radii in QQ
        self._names = names
        self._ngens = len(names)
        self._order = order
        self._integral = integral
        if integral:
            base = field.integer_ring()
        else:
            base = field
        CommutativeAlgebra.__init__(self, base, names, category=CommutativeAlgebras(base))
        self._polynomial_ring = PolynomialRing(field, names, order=order)
        one = field(1)
        self._parent_terms = TateTermMonoid(self)
        self._oneterm = self._parent_terms(one, ETuple([0]*self._ngens))
        if integral:
            self._gens = [ self((one << log_radii[i].ceil()) * self._polynomial_ring.gen(i)) for i in range(self._ngens) ]
            self._integer_ring = self
        else:
            self._gens = [ self(g) for g in self._polynomial_ring.gens() ]
            self._integer_ring = TateAlgebra_generic(field, prec, log_radii, names, order, integral=True)

    def _an_element_(self):
        r"""
        Return an element of this Tate algebra

        EXAMPLES::

            sage: A.<x,y> = TateAlgebra(Zp(2), log_radii=1)
            sage: A.an_element()  # indirect doctest
            (1 + O(2^20))*x

        """
        return self.gen()

    def _coerce_map_from_(self, R):
        r"""
        Return ``True`` if ``R`` coerces to this Tate algebra.

        INPUT:

        - ``R`` - a ring

        EXAMPLES::
        
            sage: R = Zp(2, 10, print_mode='digits'); R
            2-adic Ring with capped relative precision 10
            sage: A.<x,y> = TateAlgebra(R); A
            Tate Algebra in x (val >= 0), y (val >= 0) over 2-adic Field with capped relative precision 10

        Any ring that coerces to the base ring also coerces to the Tate
        algebra::

            sage: A.has_coerce_map_from(ZZ) # indirect doctest
            True
            sage: A.has_coerce_map_from(GF(2)) # indirect doctest
            False

        If ``R`` is also a Tate algebra, it coerces to this Tate algebra if
        the only if the base rings coerce, the variable names, the term order
        and the domain of convergence match::

            sage: S.<a> = Zq(4)
            sage: B.<x,y> = TateAlgebra(S)
            sage: B.has_coerce_map_from(A)  # indirect doctest
            True        
            sage: A.has_coerce_map_from(B) # indirect doctest
            False

        We check that coercion is not set when the variable names change::

            sage: B.<x,z> = TateAlgebra(R)
            sage: A.has_coerce_map_from(B)  # indirect doctest
            False

            sage: B.<y,x> = TateAlgebra(R)
            sage: B.has_coerce_map_from(A)  # indirect doctest
            False

        If the tame order changes, there is no coercion either::

            sage: B.<x,y> = TateAlgebra(R, order="lex")
            sage: B.has_coerce_map_from(A)  # indirect doctest
            False

        We finally check the condition on the domain of convergence::

            sage: B.<x,y> = TateAlgebra(R, log_radii=[1,-1])
            sage: B.has_coerce_map_from(A)  # indirect doctest
            False

            sage: PP.<u> = R[]
            sage: S.<pi> = R.extension(u^2 - 2)
            sage: C.<x,y> = TateAlgebra(S, log_radii=[1,-1])
            sage: C.has_coerce_map_from(B)  # indirect doctest
            False
            sage: C.<x,y> = TateAlgebra(S, log_radii=[2,-2])
            sage: C.has_coerce_map_from(B)  # indirect doctest
            True

        """
        base = self._base
        if base.has_coerce_map_from(R):
            return True
        if isinstance(R, (TateTermMonoid, TateAlgebra_generic)):
            Rbase = R.base_ring()
            logs = self._log_radii
            Rlogs = R.log_radii()
            if (base.has_coerce_map_from(Rbase)
                and self._names == R.variable_names()
                and self._order == R.term_order()):
                ratio = base.absolute_e() // Rbase.absolute_e()
                for i in range(self._ngens) :
                    if logs[i] != ratio * Rlogs[i]:
                        return False
                return True
        return False

    def _pushout_(self, R):
        """
        Return the pushout of this Tate algebra with ``R``.

        This is only implemented when ``R`` is a p-adic ring or
        a p-adic field.

        EXAMPLES::

            sage: from sage.categories.pushout import pushout
            sage: R = Zp(2)
            sage: R1.<a> = Zq(4)
            sage: R2.<pi> = R.extension(x^2 - 2)

            sage: A.<u,v> = TateAlgebra(R, log_radii=[1,2])
            sage: A1 = pushout(A, R1); A1
            Tate Algebra in u (val >= -1), v (val >= -2) over 2-adic Unramified Extension Field in a defined by x^2 + x + 1
            sage: A2 = pushout(A, R2); A2
            Tate Algebra in u (val >= -2), v (val >= -4) over 2-adic Eisenstein Extension Field in pi defined by x^2 - 2

            sage: AA = A.integer_ring()
            sage: pushout(AA, R1)
            Integer ring of the Tate Algebra in u (val >= -1), v (val >= -2) over 2-adic Unramified Extension Field in a defined by x^2 + x + 1
            sage: pushout(AA, R2.fraction_field())
            Tate Algebra in u (val >= -2), v (val >= -4) over 2-adic Eisenstein Extension Field in pi defined by x^2 - 2

        TESTS::

            sage: a*u
            (a + O(2^20))*u
            sage: (a*u).parent() is A1
            True

            sage: pi*v
            (pi + O(pi^41))*v
            sage: (pi*v).parent() is A2
            True

        """
        if isinstance(R, pAdicGeneric):
            base = pushout(self._base, R)
            ratio = base.absolute_e() // self._base.absolute_e()
            cap = ratio * self._cap
            log_radii = [ ratio * r for r in self._log_radii ]
            A = TateAlgebra(base, cap, log_radii, self._names, self._order)
            if base.is_field():
                return A
            else:
                return A.integer_ring()

    def _ideal_class_(self, n):
        r"""
        Return the class that handles ideals in this Tate algebra.

        INPUT:

        - ``n`` - number of generators

        EXAMPLE::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: A._ideal_class_(3)
            <class 'sage.rings.tate_algebra_ideal.TateAlgebraIdeal'>
        
        .. NOTE::

            The argument ``n`` is disregarded in the current implementation.
        """
        from sage.rings.tate_algebra_ideal import TateAlgebraIdeal
        return TateAlgebraIdeal

    def gen(self, n=0):
        r"""
        Return the ``n``-th generator of this Tate algebra.

        INPUT:

        - ``n`` - an integer (default: ``0``), the index of
          the requested generator

        EXAMPLES::

            sage: R = Zp(2, 10, print_mode='digits')
            sage: A.<x,y> = TateAlgebra(R)
            sage: A.gen()
            (...0000000001)*x
            sage: A.gen(0)
            (...0000000001)*x
            sage: A.gen(1)
            (...0000000001)*y
            sage: A.gen(2)
            Traceback (most recent call last):
            ...
            ValueError: generator not defined
        
        """
        try:
            return self._gens[n]
        except IndexError:
            raise ValueError("generator not defined")

    def gens(self):
        r"""
        Return the list of generators of this Tate algebra.

        EXAMPLES::

            sage: R = Zp(2, 10, print_mode='digits')
            sage: A.<x,y> = TateAlgebra(R)
            sage: A.gens()
            ((...0000000001)*x, (...0000000001)*y)
        
        """
        return tuple(self._gens)

    def ngens(self):
        """
        Return the number of generators of this algebra.

        EXAMPLES::

            sage: R = Zp(2, 10, print_mode='digits')
            sage: A.<x,y> = TateAlgebra(R)
            sage: A.ngens()
            2

        """
        return self._ngens

    def _repr_(self):
        """
        Return a printable representation of this algebra.

        EXAMPLES::

            sage: R = Zp(2, 10, print_mode='digits')
            sage: A.<x,y> = TateAlgebra(R)
            sage: A
            Tate Algebra in x (val >= 0), y (val >= 0) over 2-adic Field with capped relative precision 10
            
        """
        vars = ""
        for i in range(self._ngens):
            vars += ", %s (val >= %s)" % (self._names[i], -self._log_radii[i])
        if self._integral:
            return "Integer ring of the Tate Algebra in %s over %s" % (vars[2:], self._field)
        else:
            return "Tate Algebra in %s over %s" % (vars[2:], self._field)

    def variable_names(self):
        """
        Return the names of the variables of this algebra.

        EXAMPLES::

            sage: R = Zp(2, 10, print_mode='digits')
            sage: A.<x,y> = TateAlgebra(R)
            sage: A.variable_names()
            ('x', 'y')
        
        """
        return self._names

    def log_radii(self):
        """
        Return the list of the log-radii of convergence radii defining
        this Tate algebra.

        EXAMPLES::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: A.log_radii()
            (0, 0)

            sage: B.<x,y> = TateAlgebra(R, log_radii=1)
            sage: B.log_radii()
            (1, 1)

            sage: C.<x,y> = TateAlgebra(R, log_radii=(1,-1))
            sage: C.log_radii()
            (1, -1)

        """
        return self._log_radii

    def integer_ring(self):
        """
        Return the ring of integers (consisting of series bounded by
        1 in the domain of convergence) of this Tate algebra.

        EXAMPLES::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: AA = A.integer_ring()
            sage: AA
            Integer ring of the Tate Algebra in x (val >= 0), y (val >= 0) over 2-adic Field with capped relative precision 10

            sage: x in AA
            True
            sage: x/2 in AA
            False

        """
        return self._integer_ring

    def monoid_of_terms(self):
        """
        Return the monoid of terms of this Tate algebra.

        EXAMPLES::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: A.monoid_of_terms()
            Monoid of terms in x (val >= 0), y (val >= 0) over 2-adic Field with capped relative precision 10

        """
        return self._parent_terms

    def term_order(self):
        """
        Return the monomial order used in this algebra.

        EXAMPLES::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: A.term_order()
            Degree reverse lexicographic term order

            sage: A.<x,y> = TateAlgebra(R, order='lex')
            sage: A.term_order()
            Lexicographic term order

        """
        return self._order

    def precision_cap(self):
        """
        Return the precision cap of this Tate algebra.

        NOTE::

            The precision cap is the truncation precision
            used for arithmetic operations computed by
            successive approximations (as inversion).

        EXAMPLES:

        By default the precision cap is the precision cap of the
        field of coefficients::

            sage: R = Zp(2, 10)
            sage: A.<x,y> = TateAlgebra(R)
            sage: A.precision_cap()
            10

        But it could be different (either smaller or larger) if we
        ask to::

            sage: A.<x,y> = TateAlgebra(R, prec=5)
            sage: A.precision_cap()
            5

            sage: A.<x,y> = TateAlgebra(R, prec=20)
            sage: A.precision_cap()
            20

        """
        return self._cap

    def characteristic(self):
        """
        Return the characteristic of this algebra.

        EXAMPLES::

            sage: R = Zp(2, 10, print_mode='digits')
            sage: A.<x,y> = TateAlgebra(R)
            sage: A.characteristic()
            0

        """
        return self.base_ring().characteristic()

    def random_element(self, degree=2, terms=5, integral=False, prec=None):
        """
        Return a random element of this Tate algebra.

        INPUT:

        - ``degree`` -- an integer (default: 2), an upper bound on
          the total degree of the result

        - ``terms`` -- an integer (default: 5), the maximal number
          of terms of the result

        - ``integral`` -- a boolean (default: ``False``); if ``True``
          the result will be in the ring of integers

        - ``prec`` -- (optional) an integer, the precision of the result

        EXAMPLES::

            sage: R = Zp(2, prec=10, print_mode="digits")
            sage: A.<x,y> = TateAlgebra(R)
            sage: A.random_element()  # random
            (...00101000.01)*y + (...1111011111)*x^2 + (...0010010001)*x*y + (...110000011) + (...010100100)*y^2

            sage: A.random_element(degree=5, terms=3)  # random
            (...0101100.01)*x^2*y + (...01000011.11)*y^2 + (...00111011)*x*y

            sage: A.random_element(integral=True)  # random
            (...0001111101)*x + (...1101110101) + (...00010010110)*y + (...101110001100)*x*y + (...000001100100)*y^2

        Note that if we are already working on the ring of integers,
        specifying ``integral=False`` has no effect::

            sage: AA = A.integer_ring()
            sage: f = AA.random_element(integral=False); f  # random
            (...1100111011)*x^2 + (...1110100101)*x + (...1100001101)*y + (...1110110001) + (...01011010110)*y^2
            sage: f in AA
            True

        When the log radii are negative, integral series may have non
        integral coefficients::

            sage: B.<x,y> = TateAlgebra(R, log_radii=[-1,-2])
            sage: B.random_element(integral=True)  # random
            (...1111111.001)*x*y + (...111000101.1)*x + (...11010111.01)*y^2 + (...0010011011)*y + (...0010100011000)

        """
        if integral or self._integral:
            polring = self._polynomial_ring.change_ring(self._field.integer_ring())
            gens = self._integer_ring._gens
        else:
            polring = self._polynomial_ring
            gens = [ self.element_class(self, g) for g in self._integer_ring._gens ]
        return self.element_class(self, polring.random_element(degree, terms)(*gens), prec)
