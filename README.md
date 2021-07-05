# nizk-proof-synthesis
Python tool to construct circuits which output a non-interactive zero-knowledge proof of their correctness


### Circuit format
The proof circuit synthesis tool can parse any circuit in the standardized '[Bristol](https://homes.esat.kuleuven.be/~nsmart/MPC/) [Format](https://homes.esat.kuleuven.be/~nsmart/MPC/old-circuits.html)' which is supported by several compiled MPC libraries such as [SCALE-MAMBA](https://homes.esat.kuleuven.be/~nsmart/SCALE/).
```ada
552 680
4 32 32 32 32
1 32
2 1 31 63 128 XOR
2 1 31 63 129 AND
2 1 30 62 130 XOR
2 1 30 129 131 XOR
2 1 62 129 132 XOR
2 1 129 130 133 XOR
2 1 131 132 134 AND
...
```

### Proof structure

When a proof circuit is evaluated, it produces outputs for the original function as well as an MPC-in-the-head proof for that same computation.  Each Boolean logic gate is replaced with its equivalent set of gates that simulate it in MPC.  Here, this is done by Beaver triples and secret sharing in GF(2).  All relevant views of this MPC are collected and passed through a new implementation of LowMC (available in `LowMC_test.py`) in order to create a challenge.  Lastly, all views are indexed by the challenge, and the chosen views are outputted as the proof.


### NIZK proof circuits

As shown above, the orginial circuit is smaller by a factor of several hundred gates, depending on your security parameters.

```ada
168766 168894
4 32 32 32 32
1 2206
1 1 0 128 INV
1 1 2 129 INV
1 1 3 130 INV
1 1 4 131 INV
1 1 5 132 INV
1 1 132 133 INV
1 1 6 134 INV
...
```

All the included `nizk_*.txt` circuits were synthesized by running `python synthesis.py <circuit_name.txt>` with mainly 32-bit input sizes, but you may easily change the test input in `synthesis.py`.

The 4x32-bit variance circuit, for example, is a big as several gigabytes, yet only has a million AND gate.  The XOR-AND is very disproportional, but there are several optimization that could be implemented to improve this, as the current protocol is not optimized in any non-trivial way.