from projetobase import __version__


def run(name: str = "mundo") -> str:
    return f"Ola, {name}! ProjetoBase v{__version__}"


if __name__ == "__main__":
    print(run())
