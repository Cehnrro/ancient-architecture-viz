# 关系构建规则

1. 师承关系优先采用可考证来源（relationType=mentor）。
2. 协作关系使用同期共同工程或同机构信息（relationType=collab）。
3. 同流派关系允许受控推断（relationType=school），并强制标记 `isInferred=true`。
4. 推断关系占比上限 20%，超限时降级为可考证协作边或移除。
5. 每条关系边必须包含 `evidenceRef`，与 `heritage_sources.csv` 可对照。
