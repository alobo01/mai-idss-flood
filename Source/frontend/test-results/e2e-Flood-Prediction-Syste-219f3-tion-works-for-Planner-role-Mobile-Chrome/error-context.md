# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - button [ref=e6] [cursor=pointer]:
        - img [ref=e7]
      - generic [ref=e8]:
        - generic [ref=e9]:
          - img [ref=e10]
          - generic [ref=e12]: Flood Prediction
        - generic [ref=e13]: Planner
      - generic [ref=e14]:
        - button "Toggle dark mode" [ref=e15] [cursor=pointer]:
          - img [ref=e16]
        - button "Planner" [ref=e22] [cursor=pointer]:
          - img [ref=e23]
          - text: Planner
  - generic [ref=e26]:
    - complementary [ref=e27]:
      - navigation [ref=e28]:
        - link "Risk Map" [ref=e29] [cursor=pointer]:
          - /url: /planner/map
          - img [ref=e30]
          - generic [ref=e33]: Risk Map
        - link "Scenarios" [ref=e34] [cursor=pointer]:
          - /url: /planner/scenarios
          - img [ref=e35]
          - generic [ref=e38]: Scenarios
        - link "Alerts" [ref=e39] [cursor=pointer]:
          - /url: /planner/alerts
          - img [ref=e40]
          - generic [ref=e42]: Alerts
    - main [ref=e43]:
      - generic [ref=e45]:
        - img [ref=e46]
        - paragraph [ref=e48]: Error loading map data. Please try again.
```