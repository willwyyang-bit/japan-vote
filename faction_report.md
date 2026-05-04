# Computed Faction Report

Factions are calculated from voting similarity, not entered by hand.
An edge means two members agreed on at least 72% of common recorded votes with at least three common votes.

## Factions

- Faction 1: Fujita Mika, Ito Masato, Sato Hiroshi, Tanaka Keiko, Watanabe Shun, Yamamoto Daichi
- Faction 2: Mori Ayaka, Nakamura Yui, Suzuki Hana
- Faction 3: Kobayashi Ren

## Member Faction Signals

- Sato Hiroshi: faction_1, cohesion=0.93
- Tanaka Keiko: faction_1, cohesion=0.93
- Yamamoto Daichi: faction_1, cohesion=0.80
- Mori Ayaka: faction_2, cohesion=1.00
- Kobayashi Ren: faction_3, cohesion=0.00
- Nakamura Yui: faction_2, cohesion=1.00
- Ito Masato: faction_1, cohesion=0.93
- Suzuki Hana: faction_2, cohesion=1.00
- Watanabe Shun: faction_1, cohesion=0.93
- Fujita Mika: faction_1, cohesion=0.80

## Strong Pairwise Similarities

- Ito Masato - Sato Hiroshi: 1.00 over 6 common votes
- Ito Masato - Tanaka Keiko: 1.00 over 6 common votes
- Ito Masato - Watanabe Shun: 1.00 over 6 common votes
- Mori Ayaka - Nakamura Yui: 1.00 over 6 common votes
- Mori Ayaka - Suzuki Hana: 1.00 over 6 common votes
- Nakamura Yui - Suzuki Hana: 1.00 over 6 common votes
- Sato Hiroshi - Tanaka Keiko: 1.00 over 6 common votes
- Sato Hiroshi - Watanabe Shun: 1.00 over 6 common votes
- Tanaka Keiko - Watanabe Shun: 1.00 over 6 common votes
- Fujita Mika - Ito Masato: 0.83 over 6 common votes
- Fujita Mika - Sato Hiroshi: 0.83 over 6 common votes
- Fujita Mika - Tanaka Keiko: 0.83 over 6 common votes
- Fujita Mika - Watanabe Shun: 0.83 over 6 common votes
- Ito Masato - Yamamoto Daichi: 0.83 over 6 common votes
- Sato Hiroshi - Yamamoto Daichi: 0.83 over 6 common votes
- Tanaka Keiko - Yamamoto Daichi: 0.83 over 6 common votes
- Watanabe Shun - Yamamoto Daichi: 0.83 over 6 common votes

## Mermaid Faction Plot

```mermaid
graph LR
  m_sato_hiroshi["Sato Hiroshi"]
  m_tanaka_keiko["Tanaka Keiko"]
  m_yamamoto_daichi["Yamamoto Daichi"]
  m_mori_ayaka["Mori Ayaka"]
  m_kobayashi_ren["Kobayashi Ren"]
  m_nakamura_yui["Nakamura Yui"]
  m_ito_masato["Ito Masato"]
  m_suzuki_hana["Suzuki Hana"]
  m_watanabe_shun["Watanabe Shun"]
  m_fujita_mika["Fujita Mika"]
  m_fujita_mika -- 0.83 / 6 --- m_ito_masato
  m_fujita_mika -- 0.83 / 6 --- m_sato_hiroshi
  m_fujita_mika -- 0.83 / 6 --- m_tanaka_keiko
  m_fujita_mika -- 0.83 / 6 --- m_watanabe_shun
  m_ito_masato -- 1.00 / 6 --- m_sato_hiroshi
  m_ito_masato -- 1.00 / 6 --- m_tanaka_keiko
  m_ito_masato -- 1.00 / 6 --- m_watanabe_shun
  m_ito_masato -- 0.83 / 6 --- m_yamamoto_daichi
  m_mori_ayaka -- 1.00 / 6 --- m_nakamura_yui
  m_mori_ayaka -- 1.00 / 6 --- m_suzuki_hana
  m_nakamura_yui -- 1.00 / 6 --- m_suzuki_hana
  m_sato_hiroshi -- 1.00 / 6 --- m_tanaka_keiko
  m_sato_hiroshi -- 1.00 / 6 --- m_watanabe_shun
  m_sato_hiroshi -- 0.83 / 6 --- m_yamamoto_daichi
  m_tanaka_keiko -- 1.00 / 6 --- m_watanabe_shun
  m_tanaka_keiko -- 0.83 / 6 --- m_yamamoto_daichi
  m_watanabe_shun -- 0.83 / 6 --- m_yamamoto_daichi
```
