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

  fspec_max_len_plot:
    value: {fspec_max_len_plot}

  fspec_max_len_track:
    value: {fspec_max_len_track}

  fs:
    io: _root._io
    pos: 0
    type: field_spec(fspec_max_len_track > fspec_max_len_plot ? fspec_max_len_track:fspec_max_len_plot)

  uap_select:
    io: _root._io
    pos: fs.octects.size + (fs.flags[0].flag ? 2:0)
    type: u1

  is_track:
    value: (uap_select >> 7).as<bool>

  is_plot:
    value: not is_track

seq:
  - id: records
    type:
      switch-on: is_plot
      cases:
        true: plot_t(cat, major, minor, fspec_max_len_plot)
        false: track_t(cat, major,minor, fspec_max_len_track)
    repeat: eos

types:

{uap}

{catalogue}

