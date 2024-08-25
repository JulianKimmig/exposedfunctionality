from functools import wraps, partial
from inspect import unwrap
import sys

# heavily inspired by the functools.wraps function


# Constants defining which attributes to update under different conditions
UPDATE_IF_MISSING = (
    "__module__",
    "__name__",
    "__qualname__",
)

UPDATE_IF_EMPTY = (
    "__doc__",
    "__annotations__",
)

UPDATE_ALWAYS = ("__dict__",)


def update_wrapper(
    wrapper,
    wrapped,
    update_if_missing=UPDATE_IF_MISSING,
    update_if_empty=UPDATE_IF_EMPTY,
    never_update=(),
    update_always=UPDATE_ALWAYS,
    update_dicts=True,
    wrapper_attribute="__wrapped__",
):
    """
    Update the wrapper function to look more like the wrapped function.

    Args:
        wrapper: The function to be updated.
        wrapped: The original function being wrapped.
        update_if_missing: Attributes to update if they are missing in the wrapper.
        update_if_empty: Attributes to update if they are empty in the wrapper.
        never_update: Attributes that should never be updated.
        update_always: Attributes that should always be updated.
        update_dicts: If True, update the dictionary attributes instead of overwriting them.
        wrapper_attribute: The attribute name to use for storing the wrapped function, defaults to "__wrapped__".

    Returns:
        The wrapper function with updated attributes.
    """

    sepcial_handling = set(("__dict__",))

    # Convert to sets for easier management and subtract never_update
    never_update = set(never_update)
    never_update.add(wrapper_attribute)  # never update the wrapper attribute
    never_update.add("__wrapped__")  # never update the default __wrapped__ attribute

    update_if_empty = set(update_if_empty) - never_update
    update_if_missing = (set(update_if_missing) - never_update) | update_if_empty
    update_always = set(update_always) - never_update

    # Update attributes that are missing in the wrapper
    for attr in update_if_missing:
        if hasattr(wrapper, attr):
            continue  # Skip if wrapper already has the attribute
        try:
            value = getattr(wrapped, attr)
            setattr(wrapper, attr, value)
        except AttributeError:
            pass

    # Update attributes that are empty in the wrapper
    for attr in update_if_empty:
        wvalue = getattr(wrapper, attr, None)
        if wvalue or (
            wvalue is False or wvalue == 0
        ):  # Skip if not empty. False and 0 are considered not empty
            continue

        try:
            value = getattr(wrapped, attr)
            setattr(wrapper, attr, value)
        except AttributeError:
            pass

    # Always update specified attributes, with special handling for dictionaries
    for attr in update_always - sepcial_handling:
        try:
            value = getattr(wrapped, attr)
            if update_dicts and hasattr(wrapper, attr) and isinstance(value, dict):
                getattr(wrapper, attr).update(value)
            else:
                setattr(wrapper, attr, value)
        except AttributeError:
            pass

    # special handling for __dict__
    if "__dict__" in update_always:
        try:
            value = getattr(wrapped, "__dict__")
            # remove never_update from value
            value = {k: v for k, v in value.items() if k not in never_update}
            getattr(wrapper, "__dict__").update(value)
        except AttributeError:
            pass

    # Associate the wrapped function with the wrapper function for introspection
    setattr(wrapper, wrapper_attribute, wrapped)
    # Return the wrapper so this can be used as a decorator via partial()
    return wrapper


def controlled_wrapper(
    wrapped,
    update_if_missing=UPDATE_IF_MISSING,
    update_if_empty=UPDATE_IF_EMPTY,
    never_update=(),
    update_always=UPDATE_ALWAYS,
    update_dicts=True,
    wrapper_attribute="__wrapped__",
):
    """
    Returns a decorator that updates a wrapper function to look more like the wrapped function.

    This allows customization of which attributes are updated in the wrapper function.

    Args:
        wrapped: The original function being wrapped.
        update_if_missing: Attributes to update if they are missing in the wrapper.
        update_if_empty: Attributes to update if they are empty in the wrapper.
        never_update: Attributes that should never be updated.
        update_always: Attributes that should always be updated.
        update_dicts: If True, allows updating of dictionary attributes instead of overwriting them.
        wrapper_attribute: The attribute name to use for storing the wrapped function, defaults to "__wrapped__".

    Returns:
        A partial function that can be used as a decorator to update the wrapper function.
    """

    # Use functools.partial to create a decorator that pre-fills update_wrapper with given parameters
    return partial(
        update_wrapper,
        wrapped=wrapped,
        update_always=update_always,
        update_dicts=update_dicts,
        update_if_empty=update_if_empty,
        update_if_missing=update_if_missing,
        never_update=never_update,
        wrapper_attribute=wrapper_attribute,
    )


def controlled_unwrap(
    func, *, return_memo=False, wrapper_attribute="__wrapped__", stop=None
):
    # extended from functools.unwrap
    if stop is None:

        def _is_wrapper(f):
            return hasattr(f, wrapper_attribute)

    else:

        def _is_wrapper(f):
            return hasattr(f, wrapper_attribute) and not stop(f)

    f = func  # remember the original func for error reporting
    # Memoise by id to tolerate non-hashable objects, but store objects to
    # ensure they aren't destroyed, which would allow their IDs to be reused.
    memo = {id(f): f}
    recursion_limit = sys.getrecursionlimit()
    while _is_wrapper(func):
        func = getattr(func, wrapper_attribute)
        id_func = id(func)
        if (id_func in memo) or (len(memo) >= recursion_limit):
            raise ValueError("wrapper loop when unwrapping {!r}".format(f))
        memo[id_func] = func
    if return_memo:
        return func, memo
    return func
