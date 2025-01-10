meta:
  id: field_spec
  license: GPL-3.0-only
#  endian: be
  ks-version: 0.9

doc: |
  Implementantion of ASTERIX format.

  From Eurocontrol Asterix web page at
  https://www.eurocontrol.int/asterix

  The field_spec type, is an encapsulation of the Field Spec field. This is also
  used in the Compound format field as a primary part of the field.

params:
  - id: fspec_max_len
    type: u1

seq:
  - id: octects
    type: bits_t
    repeat: until
    repeat-until: not _.fx or octects.size == fspec_max_len

  - id: flags
    type: flags_t(octects[_index/7].bits[_index%7])
    repeat: expr
    repeat-expr: octects.size * 7

types:

  bits_t:
    seq:
      - id: bits
        type: b1
        repeat: expr
        repeat-expr: 7
      - id: fx
        type: b1

  flags_t:
    params:
      - id: flag
        type: bool

    seq: []


instances:
  size:
    value: flags.size
