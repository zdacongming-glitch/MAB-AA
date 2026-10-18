"""Append only verified references used by this revision."""
from pathlib import Path
REV=Path(__file__).resolve().parent
ROOT=REV.parent
entries=r'''
@article{waudbysmith2024betting,
  author={Waudby-Smith, Ian and Ramdas, Aaditya},
  title={Estimating means of bounded random variables by betting},
  journal={Journal of the Royal Statistical Society Series B: Statistical Methodology},
  volume={86}, number={1}, pages={1--27}, year={2024},
  doi={10.1093/jrsssb/qkad009},
  url={https://academic.oup.com/jrsssb/article/86/1/1/7043257}
}
@inproceedings{jin2021mots,
  author={Jin, Tianyuan and Xu, Pan and Shi, Jieming and Xiao, Xiaokui and Gu, Quanquan},
  title={{MOTS}: Minimax Optimal {Thompson} Sampling},
  booktitle={Proceedings of the 38th International Conference on Machine Learning},
  series={Proceedings of Machine Learning Research}, volume={139},
  pages={5074--5083}, year={2021}, publisher={PMLR},
  url={https://proceedings.mlr.press/v139/jin21d.html}
}
@inproceedings{wu2016conservative,
  author={Wu, Yifan and Shariff, Roshan and Lattimore, Tor and Szepesv{\'a}ri, Csaba},
  title={Conservative Bandits},
  booktitle={Proceedings of the 33rd International Conference on Machine Learning},
  series={Proceedings of Machine Learning Research}, volume={48},
  pages={1254--1262}, year={2016}, publisher={PMLR},
  url={https://proceedings.mlr.press/v48/wu16.html}
}
@inproceedings{garivier2011klucb,
  author={Garivier, Aur{\'e}lien and Capp{\'e}, Olivier},
  title={The {KL-UCB} Algorithm for Bounded Stochastic Bandits and Beyond},
  booktitle={Proceedings of the 24th Annual Conference on Learning Theory},
  series={Proceedings of Machine Learning Research}, volume={19},
  pages={359--376}, year={2011}, publisher={PMLR},
  url={https://proceedings.mlr.press/v19/garivier11a.html}
}
@article{thompson1933,
  author={Thompson, William R.},
  title={On the likelihood that one unknown probability exceeds another in view of the evidence of two samples},
  journal={Biometrika}, volume={25}, number={3--4}, pages={285--294}, year={1933},
  doi={10.1093/biomet/25.3-4.285},
  url={https://academic.oup.com/biomet/article-abstract/25/3-4/285/200862}
}
@misc{temporalgeometry2026,
  key={{Temporal Geometry}},
  title={The Temporal Geometry of Bandits With Arriving Arms},
  year={2026}, howpublished={Unpublished companion manuscript},
  note={Anonymized project version of October 13, 2026, with mathematical supplement}
}
'''
path=ROOT/'references.bib'
text=path.read_text(encoding='utf-8')
if '@article{waudbysmith2024betting' not in text:
    path.write_text(text.rstrip()+'\n\n'+entries.strip()+'\n',encoding='utf-8')
print('Added six verified or explicitly unpublished reference identities; retained the original bibliography.')
