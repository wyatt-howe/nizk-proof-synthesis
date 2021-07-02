# nizk-proof-synthesis
Python tool to construct circuits which output a non-interactive zero-knowledge proof of their correctness

## Results

Secure multi-party computation (MPC) allows mutually-distrusting parties to learn joint infor-mation about their secrets. MPC-in-the-head, however, allows for a single party to create apublicly-verifiable proof of a secret it knows. These two techniques can be composed to allowmultiple distrusting parties to compute a publicly-verifiable proof about some property of their joint secrets. One application is setup as follows: Users contribute data to a primary server andsecondary server in the form of XOR secret shares. An analyst may ask these servers to runa preapproved circuit on this private data. This is done within an ordinary two-party garblingexcept to prevent the servers from learning the output, the label mappings are decided at thebeginning by the analyst.  (So far this need be only an ordinary garbling.)  But now, givenour new means of evaluatingproof circuits, we may additionally insure the correctness of thisexecution (e.g.that the servers did not dishonestly modify the circuit) by having them run thegarbling protocol on a version of the original circuit which has been transformed in order to alsoproduce a (simulated MPC-in-the-head) proof.

## Future work

### Linking Security Models

If there were a way to link an execution of one protocol, semi-honest or otherwise, to an execution of a maliciously secure variant, even at a very high cost, then it would be possible to defer the execution of the proof circuit by the compute parties until they are either suspected of lying on the first execution, or a customer simply wants to order a proof.  Would a solution in the server-analyst application generalize to a larger set of protocols?  Note that this is only non-trivial when there are multiple parties involved.

### Proofs of Arithmetic Circuits

Beaver triples, garbled circuits, and MPC-in-the-head in general all support operating in _GF(n)_ rather than _GF(2)_.  We would need to write a synthesis tool for arithmetic circuits, and adapt JIGG for arithmetic circuits as well.

### Privacy Upon Collusion

It remains to be determined whether it is possible to preserve both integrity of the circuit \textit{and} privacy of the inputs upon collusion.  Circuit soldering is one avenue of investigation, as well as trying to reduce this possibility to FHE in order to rule it out.
