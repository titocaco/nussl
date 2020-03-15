from nussl.separation.base import NMFMixin
from nussl import datasets, ml, separation, evaluation
import nussl
import pytest
import numpy as np
import os

REGRESSION_PATH = 'tests/separation/regression/nmf/'
os.makedirs(REGRESSION_PATH, exist_ok=True)

def test_nmf_mixin(
    drum_and_vocals, 
    check_against_regression_data
):
    drum, vocals = drum_and_vocals
    drum.resample(16000)
    vocals.resample(16000)
    nmf = NMFMixin()

    src = drum
    mix = drum + vocals

    model, components, activations = nmf.fit(src, 20)
    tf_components, tf_activations = nmf.transform(src, model)

    reconstruction = nmf.inverse_transform(
        components, activations)

    assert np.allclose(components, tf_components)
    assert np.mean(
        (reconstruction - np.abs(src.stft())) ** 2) < 1e-4

    _, mix_activations = nmf.transform(mix, model)

    reconstruction = nmf.inverse_transform(
        components, mix_activations)
    
    mask_data = (
        reconstruction / 
        np.maximum(reconstruction, np.abs(mix.stft()))
    )
        
    mask = nussl.core.masks.SoftMask(mask_data)
    drum_est = mix.apply_mask(mask)
    drum_est.istft()
    vocals_est = mix - drum_est

    evaluator = nussl.evaluation.BSSEvalScale(
        [drum, vocals], [drum_est, vocals_est], 
        source_labels=['drums', 'vocals']
    )
    scores = evaluator.evaluate()

    reg_path = os.path.join(REGRESSION_PATH, 'nmf_mixin.json')
    check_against_regression_data(scores, reg_path)
