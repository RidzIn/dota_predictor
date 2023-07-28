def read_heroes(filename="data_processing/data/heroes/heroes.txt"):
    """
    Reads a text file containing the names of heroes and returns a set object with all the hero names.

    Parameters:
    filename (str): The name of the text file.

    Returns:
    set: A set object containing all the hero names.
    """
    hero_set = set()
    with open(filename, "r") as file:
        for line in file:
            hero_set.add(line.strip())
    return hero_set
