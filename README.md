# count-graph-homs: Yes we count!

![Count!](logo.png)

**Caption**: DALL-E is not good at spelling...

The `count-graph-homs` library is the first ever :tm: 100%-[SageMath](https://www.sagemath.org/)-compatible implementation of the homomorphism counting algorithm from "[Homomorphisms Are a Good Basis for Counting Small Subgraphs](https://arxiv.org/abs/1705.01595)" by Radu Curticapean, Holger Dell, and Dániel Marx.

The library is designed to be efficient, accurate, and user-friendly, making it ideal for students and researchers who want to incorporate graph homomorphism counting into their work. The code is well documented, so that it is potentially useful for educational purposes.

For people who are curious about *graph homomorphisms*, you are invited to read [Wikipedia](https://en.wikipedia.org/wiki/Graph_homomorphism) to get started!

- [count-graph-homs: Yes we count!](#count-graph-homs-yes-we-count)
    - [Installation](#installation)
    - [Structure](#structure)
    - [API documentation](#api-documentation)
    - [Relevant work](#relevant-work)
    - [Acknowledgements](#acknowledgements)
    - [Contributing](#contributing)
    - [License](#license)

### Installation

**Note**: We are working towards merging the code into the SageMath codebase, so that users could use it in SageMath directly.

The *current recommended way* to use the `count-graph-homs` library is from source:

```bash
git clone https://github.com/guojing0/count-graph-homs.git
cd count-graph-homs
sage -n
```

After running the above commands, you should see a SageMath (Jupyter) notebook open in your browser. You may try to run the following to see if the library is working correctly:

```python
from standard_hom_count import GraphHomomorphismCounter

square = graphs.CycleGraph(4)
bip = graphs.CompleteBipartiteGraph(2, 4)

counter = GraphHomomorphismCounter(square, bip)
count = counter.count_homomorphisms()
print(count)
```

It should print `128`, which is the correct answer.

For more details on the usage of the library, please see [tutorial.ipynb](/tutorial.ipynb) to get started.

### Structure

- **tutorial.ipynb**: A Jupyter notebook file for tutorials.
- **standard_hom_count.py**: Sequential implementation of the homomorphism counting algorithm (will be in Sage).
- **concurrent_hom_count.py**: Concurrent implementation using Dask, Numba, and Numpy (optional Sage package).
- **helpers/**: A directory of helper functions and utilities.
  - **help_functions.py**
  - **nice_tree_decomp.py**
- **deprecated/**: Deprecated codes for educational purposes only.
  - **hom_count_basic.py**
  - **hom_count_int.py**
  - **hom_count_int_dict.py**

### API documentation



### Relevant work



<!-- copenhagen impls

rust one

blair sullivan team -->

### Acknowledgements

The developer first would like to thank Radu Curticapean for his guidance and support.

This work was supported by the research grant from the European Union (ERC, CountHom, 101077083). Views and opinions expressed are those of the authors only and do not necessarily reflect those of the European Union or the European Research Council Executive Agency. Neither the European Union nor the granting authority can be held responsible for them.

### Contributing

We welcome contributions to this project! If you have found a bug or have any suggestions for improvement, please[ open an issue](https://github.com/guojing0/count-graph-homs/issues/new) or [submit a pull request](https://github.com/guojing0/count-graph-homs/compare).

### License

MIT
