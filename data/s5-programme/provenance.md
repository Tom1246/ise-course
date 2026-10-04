# S5 provenance — programme credit rules

- **Frozen artefact:** `data/s5-programme/degree-requirements.json`
- **sha256:** `36f99278312e4954129c9bd1575a794859cf1b9840268bfc3cf512a061af1dc3` (sibling `degree-requirements.json.sha256`, same format as every other frozen input)
- **Source document:** 中国科学院大学电子信息专业学位研究生培养方案（校发培养字〔2025〕92号）
  — PDF, **not committed** (a university document; the repository keeps only the extracted rules)
- **Source file identity:** 347,439 bytes, `sha256 69d6a34f9a37c2ae4623726fc4e8bb33bca36167397717e30e60fd50a0231a3d`, local copy `~/Desktop/files/工作/硕士/0854-…培养方案.pdf`
- **Extracted:** 2026-09-27, verbatim text extraction of §第二部分 硕士专业学位研究生培养方案 and
  六、必修环节及学分要求 (see the `_source` block inside the JSON for the same record)
- **Reproduce:** `python3 scripts/credit_gap.py` reads this file; `shasum -a 256` on the file above must match.

## What the hash does and does not prove

It proves the file the checks read has not changed since it was frozen, and it pins the identity of the PDF it was
transcribed from, so the same PDF can be checked again later.

It does **not** prove the transcription was faithful: the extraction was done by hand from a PDF that is not in
the repository (it is a university document, and committing it would put a third party's text in a public repo).
This is the weakest link in the I2 credit argument and is stated as such in
`doc/assignments/a2/data-governance.md` §3.5 and §7.4, rather than being hidden behind a hash.
