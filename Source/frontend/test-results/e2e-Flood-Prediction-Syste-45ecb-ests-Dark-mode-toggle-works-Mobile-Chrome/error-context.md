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
        - button "Toggle dark mode" [active] [ref=e15] [cursor=pointer]:
          - img [ref=e16]
        - button "Planner" [ref=e18] [cursor=pointer]:
          - img [ref=e19]
          - text: Planner
  - generic [ref=e22]:
    - complementary [ref=e23]:
      - navigation [ref=e24]:
        - link "Risk Map" [ref=e25] [cursor=pointer]:
          - /url: /planner/map
          - img [ref=e26]
          - generic [ref=e29]: Risk Map
        - link "Scenarios" [ref=e30] [cursor=pointer]:
          - /url: /planner/scenarios
          - img [ref=e31]
          - generic [ref=e34]: Scenarios
        - link "Alerts" [ref=e35] [cursor=pointer]:
          - /url: /planner/alerts
          - img [ref=e36]
          - generic [ref=e38]: Alerts
    - main [ref=e39]:
      - generic [ref=e41]:
        - img [ref=e42]
        - paragraph [ref=e44]: Error loading map data. Please try again.
```