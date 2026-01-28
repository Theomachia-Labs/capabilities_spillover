from csp.rubric import load_default_rubric


def test_default_rubric_loads() -> None:
    rubric = load_default_rubric()
    assert rubric.version
    assert rubric.dimensions
    assert all(dim.id for dim in rubric.dimensions)
