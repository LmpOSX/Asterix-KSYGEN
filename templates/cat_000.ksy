meta:
  id: cat_{category}_{version_major}_{version_minor}
  license: GPL-3.0-only
  endian: be
  imports:
    - field_spec
  ks-version: 0.9

doc: |
  Implementantion of ASTERIX format.

  From Eurocontrol Asterix web page at
  https://www.eurocontrol.int/asterix

  Category {category} definition file

  {title}

  {preamble}

  Edition Number: {version}

doc-ref: |
  https://www.eurocontrol.int

instances:

  cat:
    value: {cat}

  major:
    value: {major}

  minor:
    value: {minor}

  fspec_max_len:
    value: {fspec_max_len}



seq:
  - id: records
    type: record_t(cat, major, minor, fspec_max_len)
    repeat: eos

types:

  record_t:

    params:
      - id: cat
        type: u1
      - id: major
        type: u1
      - id: minor
        type: u1
      - id: fspec_max_len
        type: u1

    seq:
      - id: fspec
        type: field_spec(fspec_max_len)

{uap}

{catalogue}

