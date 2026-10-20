# IEEE Project Report

**Cloud-Native Construction Project Intelligence Platform for Predictive Delay-Risk Scoring and Real-Time Performance Analytics**

- **Authors:** Hasnain Makada (26MML0031), Sahil Mall (26MML0049), Aryan Kishor Sao (26MML0046)
- **Affiliation:** School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, India
- **Guide:** Dr. Manikandan K, Professor Grade 2, Department of Database Systems, SCSE, VIT Vellore
- **Format:** IEEE conference style (IEEEtran), 15 pages

## Files
| File | Purpose |
|------|---------|
| `main.tex` | LaTeX source (all 12 required sections) |
| `main.pdf` | Compiled report (15 pages) |
| `references.bib` | BibTeX references (IEEE style) |
| `IEEEtran.cls`, `IEEEtran.bst` | IEEE document class + bibliography style |
| `figures/` | Dashboard screenshots used as figures |

## Sections
1. Title / Team / Guide
2. Abstract
3. Introduction (motivation, problem statement, research questions)
4. System Model & Architecture (formal model, data dictionary, ER diagram, topology)
5. Literature Review & Related Works
6. Existing Approach (failure-mode analysis, requirements traceability, positioning)
7. Proposed Design (EVM, delay-risk modeling, reliability formulation, algorithm)
8. Implementation (services, API, error handling, deployment, generator)
9. Result Analysis (metrics, classifier comparison, EVM correctness, validity threats)
10. Conclusion
11. Future Work
12. References

## Regenerate the PDF
```bash
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```
Requires a TeX distribution with `IEEEtran.cls` (bundled here) and packages: booktabs, tikz, pgfplots, hyperref.

## Reproducibility
Every number in the report comes from a real run of the platform:
```bash
cd ../platform && ./run.sh          # generates data, runs pipeline, serves dashboard
```
Classifier metrics: `python -m eval.benchmark_models`. Screenshots in `../docs/screenshots/`.
