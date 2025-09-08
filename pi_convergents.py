"""
================================================================================
An Exploration of π Approximations via Continued Fractions of its Powers
================================================================================

This script serves as a detailed, educational guide to an elegant method for
finding highly accurate rational approximations of π (pi).

-----------------
The Core Idea
-----------------
The fundamental goal is to find integer powers of π, denoted as π^k, that are
themselves very close to a simple rational number (a fraction p/q).

  π^k ≈ p/q

If we can find such a fraction where the difference between π^k and p/q is
extremely small, we can rearrange the formula by taking the k-th root of
both sides to find a novel approximation for π:

  π ≈ (p/q)^(1/k)

This method can yield surprisingly simple and accurate approximations, like the
one mentioned in the original problem: π ≈ (2143/22)^(1/4).

-----------------
Finding the "Best" Rational Approximations: Convergents
-----------------
How do we find these "best" rational numbers p/q that are close to a given
value x (like π^k)? The most powerful tool for this is the continued fraction.

A continued fraction represents a number as a sequence of integers, like so:
  x = a₀ + 1/(a₁ + 1/(a₂ + 1/(a₃ + ...)))

The "convergents" of a continued fraction are the sequence of rational numbers
you get by cutting off this expansion at each step. For example, the famous
approximations 22/7 and 355/113 are convergents of the continued fraction of π.

The magic of convergents is that they are, in a very precise sense, the *best
possible* rational approximations for a number. The n-th convergent is closer
to the target number x than any other fraction with a smaller denominator.

-----------------
The Algorithm Implemented Below
-----------------
1.  **Calculate π^k**: We start with a high-precision value of π, raise it to
    the integer power `k` we are interested in.

2.  **Compute the Continued Fraction**: We use a simple iterative algorithm to
    find the integer coefficients (a₀, a₁, a₂, ...) of the continued fraction
    for π^k.
    - Let x be our number (initially π^k).
    - The next coefficient is the integer part of x: aᵢ = floor(x).
    - The new x becomes the reciprocal of the fractional part: x = 1/(x - aᵢ).
    - We repeat this process to generate the sequence of coefficients.

3.  **Calculate the Convergents**: From the sequence of coefficients, we
    generate the sequence of convergents (pₙ/qₙ). These are calculated using a
    simple recurrence relation, which is much easier than expanding the full
    fraction each time:
    - pₙ = aₙ * pₙ₋₁ + pₙ₋₂
    - qₙ = aₙ * qₙ₋₁ + qₙ₋₂
    This generates the sequence of "best" rational approximations for π^k.

4.  **Derive the π Approximation**: For each convergent p/q, we calculate the
    final approximation for π using the formula (p/q)^(1/k) and check its
    accuracy against the true value of π.

This script provides functions to perform each of these steps and then uses
them to find approximations of a desired accuracy.
"""

import math

def get_continued_fraction(x, max_terms=15):
    """
    Calculates the continued fraction coefficients for a given number x.

    The algorithm works by repeatedly separating the number into its integer
    and fractional parts. The integer part is the next coefficient, and the
    process is repeated on the reciprocal of the fractional part.

    Args:
        x (float): The number to convert.
        max_terms (int): The maximum number of coefficients to generate.

    Returns:
        list: A list of integer coefficients of the continued fraction.
    """
    coefficients = []
    # Ensure we are working with floating point numbers for precision.
    remainder = float(x)

    for _ in range(max_terms):
        # The integer part of the remainder is the next coefficient.
        a = int(math.floor(remainder))
        coefficients.append(a)

        # Subtract the integer part to get the fractional part.
        fractional_part = remainder - a

        # If the fractional part is very close to zero, the number is rational
        # and we have found the exact representation.
        if math.isclose(fractional_part, 0):
            break

        # The new remainder for the next iteration is the reciprocal of the
        # fractional part.
        remainder = 1.0 / fractional_part

    return coefficients


def get_convergents(cf_coefficients):
    """
    Calculates the convergents from a list of continued fraction coefficients.

    This function uses the fundamental recurrence relation for convergents.
    Given the n-th convergent pₙ/qₙ and coefficient aₙ:
    pₙ = aₙ * pₙ₋₁ + pₙ₋₂
    qₙ = aₙ * qₙ₋₁ + qₙ₋₂

    The initial ("seed") values are set as:
    p₋₂ = 0, p₋₁ = 1
    q₋₂ = 1, q₋₁ = 0

    Args:
        cf_coefficients (list): A list of continued fraction coefficients.

    Yields:
        tuple: A tuple (p, q) for each convergent p/q.
    """
    # Seed values for the recurrence relation.
    p_prev2, p_prev1 = 0, 1
    q_prev2, q_prev1 = 1, 0

    for a in cf_coefficients:
        # Calculate the next p and q based on the previous two values.
        p = a * p_prev1 + p_prev2
        q = a * q_prev1 + q_prev2

        # Update the previous values for the next iteration.
        p_prev2, p_prev1 = p_prev1, p
        q_prev2, q_prev1 = q_prev1, q

        # Yield the current convergent as a (p, q) tuple.
        yield (p, q)


def find_pi_approximation_to_d_digits(k, D):
    """
    Finds the simplest rational approximation p/q for π^k that yields an
    approximation of π accurate to at least D digits.

    Args:
        k (int): The power to raise π to (e.g., 4 for π^4).
        D (int): The desired number of correct digits after the decimal point.

    Returns:
        dict: A dictionary containing the results, including the power k, the
              convergent (p, q), the π approximation, and the error.
    """
    # The required tolerance for D digits of accuracy.
    # For example, for 2 digits, we need the error to be less than 0.01.
    tolerance = 10**(-D)

    # Calculate the target value, π^k.
    target_value = math.pi ** k

    # Start with a reasonable number of terms for the continued fraction.
    num_terms = 2
    while True:
        # Generate the continued fraction for π^k. We may need more terms if
        # the initial convergents are not accurate enough.
        cf = get_continued_fraction(target_value, max_terms=num_terms)

        # Calculate all convergents for this set of coefficients.
        convergents = list(get_convergents(cf))

        # We only need to check the last (and most accurate) convergent.
        p, q = convergents[-1]

        # Avoid division by zero, although this is highly unlikely for π^k.
        if q == 0:
            num_terms += 1
            continue

        # Calculate our approximation for π.
        pi_approx = (p / q) ** (1 / k)
        error = abs(pi_approx - math.pi)

        # Check if the approximation is within the desired tolerance.
        if error < tolerance:
            return {
                "power_k": k,
                "digits_D": D,
                "convergent_p": p,
                "convergent_q": q,
                "pi_approximation": pi_approx,
                "error": error
            }

        # If not accurate enough, increase the number of terms and try again.
        num_terms += 1
        # To prevent an infinite loop in case of issues, let's add a limit.
        if num_terms > 50:
             return {"error": "Could not find a suitable approximation."}


if __name__ == "__main__":
    print("=" * 60)
    print("Demonstration: Finding approximations for π using π^k")
    print("=" * 60)

    # --- Part 1: Detailed breakdown for a specific k, e.g., k=6 ---
    K_DEMO = 6
    pi_to_k = math.pi ** K_DEMO
    print(f"\nAnalyzing for k = {K_DEMO}, so we target π^{K_DEMO} ≈ {pi_to_k:.8f}\n")

    # Step 1 & 2: Get continued fraction for π^6
    cf_pi6 = get_continued_fraction(pi_to_k, max_terms=10)
    print(f"Continued Fraction for π^{K_DEMO}: [", end="")
    print(*cf_pi6, sep='; ', end=']\n\n')

    # Step 3 & 4: Get convergents and check π approximations
    print("Convergents for π^6 and resulting π approximations:")
    print("-" * 60)
    print(f"{'Convergent (p/q)':<20} | {'π Approx (p/q)^(1/{K_DEMO})':<28} | {'Error':<15}")
    print("-" * 60)

    for p, q in get_convergents(cf_pi6):
        if q == 0: continue
        pi_approx = (p / q) ** (1 / K_DEMO)
        error = abs(pi_approx - math.pi)
        print(f"{p:>8}/{q:<10} | {pi_approx:<28.15f} | {error:<15.2e}")

    print("\n" + "=" * 60)
    print("Goal: Find the simplest p, q for various k")
    print("      that give π accurate to D=8 decimal places.")
    print("=" * 60 + "\n")

    # --- Part 2: Use the helper function to find results for different k ---
    for k_val in [4, 5, 6, 7]:
        print(f"Searching for k = {k_val}...")
        result = find_pi_approximation_to_d_digits(k=k_val, D=8)

        # *** BUG FIX ***
        # The original code had a flawed check here. A successful result also
        # contains the key "error" (with a float value), which caused a
        # TypeError.
        # The corrected logic now checks for a key that ONLY exists in a
        # successful result dictionary ('convergent_p') to distinguish it
        # from a failure.
        if 'convergent_p' in result:
            p = result['convergent_p']
            q = result['convergent_q']
            approx = result['pi_approximation']
            err = result['error']

            print(f"  > Found for π^{k_val}: p={p}, q={q}")
            print(f"  > π ≈ ({p}/{q})^(1/{k_val})")
            print(f"  > Approximation: {approx:.12f}")
            print(f"  > Error: {err:.2e}\n")
        else:
            # This block now correctly handles the failure case.
            print(f"  > Could not find an approximation for k={k_val}.")
