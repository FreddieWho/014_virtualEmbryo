"""Training-only validation helpers; never accept heldout outcomes as features."""
import numpy as np


def training_response_sd(responses, train_genes, heldout):
    train_genes = tuple(train_genes)
    if heldout in train_genes:
        raise ValueError('heldout response present in training identities')
    if len(train_genes) < 2 or len(set(train_genes)) != len(train_genes):
        raise ValueError('need at least two unique training perturbations')
    return np.std(np.stack([responses[g] for g in train_genes]), axis=0)


def nearest_training_donor(embedding, names, train_genes, query):
    """Exactly the delivery GO-dot-product rule, restricted to outer training IDs."""
    if query in train_genes:
        raise ValueError('heldout condition admitted as its own donor')
    index = {g: i for i, g in enumerate(names)}
    train_genes = tuple(train_genes)
    if not train_genes:
        raise ValueError('empty donor set')
    return max(train_genes, key=lambda g: float(embedding[index[query]] @ embedding[index[g]]))


def signed_program_pair(H, delta):
    """Return (remove, add): anti-aligned program decreases, aligned one increases.

    None denotes no supported program in the requested signed direction. This
    prevents a same-sign second-best program being mislabeled an opposite program.
    """
    H, delta = np.asarray(H), np.asarray(delta)
    if delta.std() <= 0:
        return None, None
    c = np.array([np.corrcoef(h, delta)[0, 1] if h.std() > 0 else 0. for h in H])
    remove = int(np.argmin(c)) if np.min(c) < -1e-12 else None
    add = int(np.argmax(c)) if np.max(c) > 1e-12 else None
    return remove, add
