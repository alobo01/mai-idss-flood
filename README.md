# Flood-IDSS: Intelligent Decision Support System for Flood Management

## Project Overview

Flood-IDSS is an intelligent decision support system designed to assist in flood risk assessment, prediction, and management. This project leverages machine learning and data analytics to provide actionable insights for flood prevention and response strategies.

## Goals

- **Risk Assessment**: Analyze historical and real-time data to assess flood risks in different regions
- **Prediction Models**: Develop machine learning models to predict flood events and their severity
- **Decision Support**: Provide interactive tools and dashboards for decision-makers
- **Data Integration**: Integrate multiple data sources (meteorological, hydrological, geographical)
- **Visualization**: Create intuitive visualizations for complex flood-related data

## Project Structure

```
mai-idss-flood/
├── Documentation/     # Project documentation, reports, and technical specifications
├── Data/             # Raw and processed datasets (excluded from version control)
├── Models/           # Trained ML models and model artifacts
├── Source/           # Source code for data processing, models, and applications
├── Demo/             # Demo scripts and sample applications
├── Presentation/     # Presentation materials, slides, and visual assets
├── README.md         # This file
├── requirements.txt  # Python dependencies
└── .gitignore       # Git ignore rules
```

### Directory Descriptions

- **Documentation/**: Contains all project documentation including design documents, API specifications, user guides, and weekly progress reports.

- **Data/**: Houses all data files including raw datasets, processed data, and intermediate outputs. Note: Data files are excluded from version control to maintain repository size.

- **Models/**: Stores trained machine learning models, model checkpoints, and serialized model artifacts.

- **Source/**: Contains all source code organized by functionality (data preprocessing, feature engineering, model training, API endpoints, web application).

- **Demo/**: Includes demonstration scripts, Jupyter notebooks, and sample applications showcasing system capabilities.

- **Presentation/**: Contains presentation slides, figures, diagrams, and other materials for project presentations and deliverables.

## Technology Stack

- **Python 3.x**: Core programming language
- **Streamlit**: Interactive web application framework
- **FastAPI**: High-performance API framework
- **scikit-learn**: Machine learning library
- **Additional libraries**: See `requirements.txt` for complete list

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alobo01/mai-idss-flood.git
   cd mai-idss-flood
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   # For the Streamlit dashboard
   streamlit run Source/app.py
   
   # For the FastAPI backend
   uvicorn Source.api:app --reload
   ```

## Development Workflow

### Branching Strategy

- **dev**: Main development branch for collaboration
- Feature branches: Create from `dev` for new features
- Pull requests: Required for all changes to `dev`

### Weekly Deliverables

1. Create a feature branch from `dev`
2. Implement changes and commit regularly
3. Submit a pull request with detailed description
4. Code review and merge to `dev`

### Contribution Guidelines

- Follow PEP 8 style guide for Python code
- Write descriptive commit messages
- Document all functions and classes
- Include tests for new functionality
- Update documentation as needed

### Gantt Diagram:
``m̀ermaid
---
displayMode: broad
---
gantt
    title PW3 IDSS Project — 3-Week Plan (Broad View)
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    excludes weekends
    tickInterval 1week
    todayMarker stroke-width:3px,stroke:#ff6600,opacity:0.6

    section Week 1
    Frontend mock-up (1)           :p1w1, 2025-11-10, 5d
    Data inspection & visualization (2) :p3w1, 2025-11-10, 5d
    IDSS architecture & influence diagram (1) :p5w1, 2025-11-10, 5d
    Research & rule-based design (2) :p6w1, 2025-11-10, 5d

    section Week 2 
    Backend prototype (2)          :p1w2, after p6w1, 5d
    Model training & metrics (3)   :p4w2, after p3w1, 5d
    Evaluation framework (1)       :p5w2, after p5w1, 5d

    section Week 3 
    Integration demo (2.5)       :p1w3, after p1w2 p2w2, 5d
    Evaluation execution (2.5)   :p4w3, after p5w2, 5d
    Canva, report outline (1)            :p6w3, after p5w2, 5d
    Documentation & slides (All)    :done, after p1w3 p4w3 p6w3, 2d

    section Milestones
    Foundations complete            :milestone, m1, after p6w1, 0d
    Modeling phase complete         :milestone, m2, after p6w2, 0d
    Final integration & submission  :milestone, m3, after p6w3, 0d
```
## Team

- Project repository: [alobo01/mai-idss-flood](https://github.com/alobo01/mai-idss-flood)

## License

[Add license information here]

## Contact

[Add contact information here]
