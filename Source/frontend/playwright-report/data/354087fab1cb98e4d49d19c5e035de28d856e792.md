# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - button [ref=e6] [cursor=pointer]:
        - img [ref=e7]
      - generic [ref=e11]:
        - generic [ref=e12]:
          - img [ref=e13]
          - generic [ref=e17]: Flood Prediction
        - generic [ref=e18]: Planner
      - generic [ref=e19]:
        - button "Toggle dark mode" [ref=e20] [cursor=pointer]:
          - img [ref=e21]
        - button "Planner" [ref=e31] [cursor=pointer]:
          - img [ref=e32]
          - text: Planner
  - generic [ref=e35]:
    - complementary [ref=e36]:
      - navigation [ref=e37]:
        - link "Risk Map" [ref=e38] [cursor=pointer]:
          - /url: /planner/map
          - img [ref=e39]
          - generic [ref=e42]: Risk Map
        - link "Scenarios" [ref=e43] [cursor=pointer]:
          - /url: /planner/scenarios
          - img [ref=e44]
          - generic [ref=e47]: Scenarios
        - link "Alerts" [ref=e48] [cursor=pointer]:
          - /url: /planner/alerts
          - img [ref=e49]
          - generic [ref=e53]: Alerts
    - main [ref=e54]:
      - generic [ref=e56]:
        - img [ref=e57]
        - paragraph [ref=e61]: Error loading map data. Please try again.
```