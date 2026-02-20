Software Requirements Specification (SRS)
Project Name
E-Habitat: Interactive Server Room Monitoring Simulator
Client / Sponsor
Self-Proposed (Educational Project)
Team Members
Logan Caraballo — Project Lead / Backend
Jared He — Frontend / UI
Gavin Paeth — Simulation, Data, Testing
Document Version
Proposal-Safe MVP Revision v1.1
Last Updated: 2026-02-01

1. Executive Summary
   1.1 Project Overview
   E-Habitat is an interactive educational simulation platform designed to help learners understand distributed systems concepts by comparing centralized and edge-based monitoring architectures in a realistic server room environment. The system simulates thermal, airflow, and humidity dynamics across multiple virtual nodes and visualizes how different monitoring strategies detect anomalies under identical conditions. E-Habitat enables hands-on exploration of architectural tradeoffs without requiring physical infrastructure.
   1.2 Problem Statement
   Students studying distributed systems often encounter abstract concepts such as edge computing, centralized monitoring, latency, and bandwidth tradeoffs without access to realistic experimentation environments. Existing tools are either production-grade monitoring systems that are too complex for educational use or purely theoretical materials that lack experiential learning. This gap limits students’ ability to develop intuition about real-world distributed system behavior.
   1.3 Solution Overview
   E-Habitat addresses this gap by providing a controlled, visual, and interactive simulation where centralized and edge monitoring architectures operate simultaneously on the same environmental data. By allowing users to inject anomalies and observe detection latency, bandwidth usage, and system behavior in real time, the platform makes distributed systems principles concrete and observable.
   1.4 Client Context (Self‑Proposed)
   This project is self-proposed and intended for use by computer science students, instructors, and self-learners in academic settings. The primary success criteria are educational clarity, ease of setup, and the ability to demonstrate architectural tradeoffs during live demos or guided lab exercises. Requirements and scope were validated against typical distributed systems course objectives and instructor-led demonstration needs.

2. User Research & Personas
   2.1 Research Basis
   User needs were identified through course experience, review of distributed systems curricula, and analysis of existing monitoring and simulation tools. Common findings include the need for visual feedback, repeatable experiments, and simplified interfaces that focus on architectural behavior rather than operational complexity.
   2.2 User Personas
   Primary Persona: Computer Science Student
   Background: Upper-level undergraduate or graduate student studying distributed systems or related topics
   Technical Proficiency: Intermediate
   Needs:
   Observe how centralized and edge monitoring differ under the same conditions
   Experiment with anomalies and interpret system behavior
   Pain Points:
   Abstract concepts without hands-on reinforcement
   Lack of accessible simulation tools
   Goals:
   Develop intuition about latency, bandwidth, and fault handling
   Technology Context: Laptop running a local development environment
   Secondary Persona: Course Instructor
   Background: University-level instructor teaching systems courses
   Technical Proficiency: Advanced
   Needs:
   Reliable classroom demonstrations
   Controlled scenarios to illustrate specific concepts
   Goals:
   Reinforce lecture material with visual, repeatable experiments
   Technology Context: Classroom or personal workstation

3. User Stories
   Note: The MVP explicitly excludes user accounts, authentication, and multi-user persistence. All interactions occur within a single local session.
   Core Feature: Simulation Control
   US001: As a user, I want to start and stop a simulation so that I can observe environmental behavior in real time.
   Telemetry begins streaming within one second of start
   Simulation runs at one-second time steps
   US002: As a user, I want to configure baseline environmental parameters so that I can explore different operating conditions.
   Users can set temperature, airflow, and humidity ranges before simulation start
   Invalid values are rejected with clear feedback
   Core Feature: Anomaly Interaction
   US003: As a user, I want to inject predefined anomaly scenarios so that I can observe how each architecture responds.
   Thermal spike and HVAC failure scenarios are supported
   Visual indicators show when anomalies occur
   Core Feature: Architecture Comparison
   US004: As a user, I want to view centralized and edge monitoring results side by side so that I can compare tradeoffs.
   Both architectures run simultaneously on identical data
   Comparison metrics include detection latency and message volume
   Core Feature: Visualization
   US005: As a user, I want to view real-time telemetry and alerts so that I can interpret system behavior.
   Live charts update with less than 200ms latency
   Alerts appear when anomalies are detected

4. Features & Requirements
   4.1 Core Features
   Simulation Engine — Simulates thermal, airflow, and humidity dynamics across three virtual nodes at one-second intervals.
   Dual Monitoring Architectures — Centralized raw-telemetry streaming and edge-based local anomaly detection running concurrently.
   Anomaly Scenarios — Two predefined anomaly scenarios with manual injection controls.
   Real-Time Dashboard — Displays telemetry, alerts, and architecture comparison metrics.
   Educational Comparison Metrics — Detection latency and network message volume for each architecture.
   4.2 Functional Requirements
   The system shall simulate at least three virtual nodes concurrently.
   The system shall stream telemetry using WebSockets.
   The system shall compute anomaly scores using a pre-trained Isolation Forest model.
   The system shall display alerts when anomaly thresholds are exceeded.
   4.3 Non-Functional Requirements
   Performance
   Dashboard updates shall occur with less than 200ms latency.
   The system shall support at least three nodes without dropped messages.
   Usability
   The interface shall support live demos without prior configuration.
   Core actions shall be accessible within two clicks.
   Reliability
   The system shall run continuously for at least one hour without failure.
   Security (MVP Assumptions)
   The MVP assumes a trusted local execution environment.
   No authentication or authorization is required in MVP scope.

5. System Design
   5.1 Technology Stack
   Backend: Python 3.10+, FastAPI, WebSockets
   Frontend: React 18, Material-UI, Recharts
   Database: SQLite (time-series telemetry)
   ML: scikit-learn Isolation Forest
   5.2 High-Level Architecture
   [Physics Engine] → [Virtual Nodes] → [WebSocket Bus] → [FastAPI Backend] → [SQLite] → [React Dashboard]
   5.3 User Interface Overview
   Dashboard: Telemetry charts, alerts, comparison metrics
   Controls Panel: Start/stop simulation, inject anomaly
   5.4 Physics Models
   Our simulation models three interconnected environmental factors:
   Thermal Model:
   Heat Transfer: Q = m·c·ΔT
   Server Heat Output: P_heat = k·CPU_load
   Temperature Update: T(t+1) = T(t) + (P_heat - CoolingPower) / (AirMass·c)

Airflow Model:
Airflow Drop from Blockage: Flow_new = Flow_nominal·(1 - ObstructionRatio)
Fan Failure: Flow_new = 0

Humidity Model:
H(t+1) = H(t) + Drift + Noise

5.5 Validation Against Real Data
To ensure realistic simulation behavior, we validate physics parameters against real-world datasets:
MIT CSAIL Intel Lab Sensor Dataset:
54 sensors deployed in lab environment (2004)
Provides: temperature, humidity, light, voltage readings
Usage: Extract baseline temperature/humidity ranges and variance patterns to seed our normal operating conditions
Specific Integration: Calculate mean/std of temperature (typically 19-24°C) and humidity (30-50% RH) to set simulation defaults
U.S. DOE Data Center Thermal Dataset:
Real data center thermal measurements
Usage: Validate our thermal model's heat dissipation rates against actual server room behavior
Specific Integration: Compare our simulated thermal responses to CPU load changes against DOE measurements to tune heat output coefficient (k)
Kaggle HVAC System Dataset:
HVAC operation data including airflow and cooling patterns
Usage: Calibrate cooling system response curves and airflow dynamics
Specific Integration: Extract cooling power curves as function of temperature differential to model realistic HVAC behavior
Implementation Plan:
Week 2: Download and process datasets, extract statistical summaries
Week 3: Tune physics parameters against real data distributions
Week 4: Validate simulation output matches real-world patterns (temperature rise rates, humidity stability, cooling effectiveness)

6. Data Integration & Anomaly Detection
   6.1 Real Dataset Integration Plan
   Phase 1: Baseline Calibration (Week 2)
   Extract normal operating ranges from all three datasets
   Calculate statistical distributions (mean, variance, percentiles)
   Set simulation default parameters to match real-world baselines
   Phase 2: Physics Validation (Week 3)
   Run simulation with real-world parameters
   Compare synthetic output distributions to real data
   Tune heat transfer coefficients, cooling rates, and noise levels
   Phase 3: Anomaly Model Training (Week 4)
   Generate 48 hours of synthetic normal operation telemetry
   Combine with normal periods extracted from real datasets
   Train Isolation Forest on merged normal data
   Validate detection on known anomalies from real datasets
   6.2 Anomaly Detection Pipeline
   Training (Offline):
   Generate baseline telemetry using physics engine with real-data parameters
   Extract sliding-window features (10-second windows)
   Train Isolation Forest on normal operation only
   Save model as .pkl artifact for deployment
   Inference (Real-Time During Simulation):
   Nodes collect telemetry in sliding windows
   Extract features (mean, variance, rate-of-change)
   Run Isolation Forest prediction
   If anomaly score exceeds threshold → trigger alert
   Transmit alert (edge) or raw data (centralized) to backend
   Why Isolation Forest:
   Unsupervised: doesn't require labeled anomalies
   Fast: suitable for real-time edge inference
   Interpretable: anomaly scores are understandable
   Proven: widely used in production anomaly detection
   Limitations Acknowledged:
   Detects deviations, doesn't predict future events
   Threshold tuning required for different scenarios
   May produce false positives on rare-but-normal events
   More sophisticated models (LSTM, Autoencoder) deferred to post-capstone

7. Testing & Validation
   7.1 Testing Approach
   Unit Tests (Target: Core Logic Coverage)
   Physics engine calculations (thermal, airflow, humidity updates)
   Feature extraction functions (sliding window, statistics)
   Anomaly detection inference (model loading, prediction)
   WebSocket message formatting/parsing
   Integration Tests
   End-to-end simulation flow: engine → nodes → backend → database
   WebSocket communication reliability
   Dashboard receiving and displaying real-time updates
   Anomaly injection triggering alerts in both architectures
   Performance Benchmarks
   3-node simulation runs smoothly (>10 FPS simulation speed)
   Dashboard updates with <200ms latency
   WebSocket handles 30+ messages/second without dropping
   System runs continuously for 1+ hour without crashes
   Validation Tests
   Physics output matches real-world data distributions
   Anomaly detection triggers on injected scenarios
   Both architectures produce alerts for same anomalies
   Comparison metrics calculate correctly
   7.2 Software Quality Metrics
   Success Criteria:
   Simulation runs 3 nodes with realistic physics
   Both architectures operational and comparable
   2+ anomaly scenarios working reliably
   Dashboard updates in real-time (<200ms latency)
   Detection latency and bandwidth metrics display correctly
   New user can run first simulation in <20 minutes following README
   Unit test coverage for physics and detection logic
   Zero crashes during 30-minute demo scenario
   Quality Targets:
   Code follows PEP 8 (Python) and ESLint (JavaScript)
   All public functions have docstrings
   Critical paths have error handling
   Git commits are meaningful and atomic
   7.3 User Acceptance Testing
   Week 11: Usability Testing
   2-3 external testers (classmates not on team)
   Tasks: Install, run simulation, inject anomaly, interpret results
   Collect feedback on: setup clarity, UI intuitiveness, comparison usefulness
   Iterate on documentation and UI based on feedback
   Week 12: Final Validation
   Professor Cain demos all core scenarios
   Verify all success criteria met
   Confirm documentation enables independent use

8. Project Timeline & Work Plan
   Sprint 1 (Weeks 1-4): Foundation
   Goals: Working single-node simulation with basic physics and data pipeline
   Week 1:
   Finalize architecture decisions
   Set up development environment and repository
   Download and process real datasets
   Implement basic physics engine (thermal only)
   Week 2:
   Complete physics engine (airflow, humidity)
   Validate against real data distributions
   Single virtual node prototype
   Basic FastAPI WebSocket endpoint
   Week 3:
   Train initial Isolation Forest model
   Implement local anomaly detection on node
   Test centralized data flow: node → backend → storage
   Week 4:
   Basic dashboard with live charts
   Manual anomaly injection (thermal spike)
   End-to-end testing of single-node system
   Sprint 1 Deliverable: Demo of 1 node streaming data, detecting injected thermal anomaly, displaying on dashboard

Sprint 2 (Weeks 5-8): Multi-Node & Architecture Comparison
Goals: 3-node system with both architectures operational
Week 5:
Expand to 3 virtual nodes
Implement edge architecture (local detection, score transmission)
WebSocket multiplexing for multiple nodes
Week 6:
SQLite schema and time-series storage
Backend alert routing and aggregation
Dashboard showing all 3 nodes simultaneously
Week 7:
Second anomaly scenario (HVAC failure)
Architecture comparison panel on dashboard
Detection latency and bandwidth metrics
Week 8:
Integration testing and bug fixes
Performance optimization
Documentation (README, architecture diagram)
Sprint 2 Deliverable: Demo of 3 nodes, both architectures running, comparison metrics showing latency and bandwidth differences

Sprint 3 (Weeks 9-12): Polish, Testing & Finalization
Goals: Production-ready demo, comprehensive testing, complete documentation
Week 9:
Third anomaly scenario if time permits (airflow blockage)
Comprehensive testing (unit, integration, performance)
Dashboard UI refinements
Week 10:
User acceptance testing with external testers
Bug fixes based on feedback
Documentation improvements
Week 11:
Final integration testing
Demo rehearsal and scenario preparation
Presentation materials
Week 12:
Final demo
Code cleanup and final documentation
Project submission
Sprint 3 Deliverable: Complete, tested, documented system ready for demonstration and educational use

9. Technical Risks & Mitigation Strategies
   9.1 High-Risk Items
   Risk 1: Physics Engine Complexity Exceeds Timeline
   Impact: Core simulation doesn't work realistically, undermines entire project
   Probability: Medium
   Mitigation:
   Start with simplified thermal-only model in Week 1
   Validate against real data early (Week 2)
   If complex physics takes >3 weeks, simplify models using lookup tables instead of differential equations
   Contingency: Use temperature only; defer humidity/airflow to post-capstone
   Risk 2: WebSocket Performance Issues at Scale
   Impact: Dashboard lags or drops messages with multiple nodes
   Probability: Low-Medium
   Mitigation:
   Test with 3 nodes early (Week 5)
   Implement message batching if needed
   Use existing WebSocket libraries (avoid custom protocols)
   Contingency: Reduce to 2 nodes for demo, or use HTTP polling instead of WebSockets
   Risk 3: Real-Time Dashboard Responsiveness
   Impact: Charts stutter, poor user experience
   Probability: Medium
   Mitigation:
   Use proven charting library (Recharts) optimized for real-time
   Limit chart history to last 5 minutes
   Throttle updates to 1-2 per second
   Contingency: Dashboard shows delayed data (5-10 second lag acceptable), or snapshot updates instead of streaming
   Risk 4: SQLite Performance for Time-Series Data
   Impact: Query slowdowns, storage bottlenecks
   Probability: Low
   Mitigation:
   Keep simulation duration short (<1 hour)
   Index timestamp columns
   Batch inserts
   Contingency: Write-only database during simulation, analysis afterward; or switch to in-memory storage
   9.2 Medium-Risk Items
   Risk 5: Team Member Availability
   Impact: Work falls behind schedule
   Mitigation: Weekly standups, clear task assignments, parallel workstreams
   Contingency: Reduce MVP scope (drop third anomaly scenario, simplify dashboard)
   Risk 6: Integration Challenges Between Components
   Impact: Components work separately but fail together
   Mitigation: Integration testing starting Week 4, frequent end-to-end testing
   Contingency: Simplify interfaces, use polling instead of real-time where needed
   Risk 7: Anomaly Detection Produces Too Many False Positives
   Impact: Demo shows useless alerts, undermines educational value
   Mitigation: Tune Isolation Forest threshold during validation (Week 4)
   Contingency: Use simple rule-based detection (threshold crossings) instead of ML
   9.3 Feature Prioritization Plan
   If timeline slips, cut features in this order:
   Third anomaly scenario (airflow blockage)
   Advanced dashboard features (historical playback, exports)
   5th node (reduce to 3)

10. Success Metrics
    Software Application:
    Simulation starts successfully within 10 seconds of launch
    Anomalies detected in both architectures during demos
    New users can run a complete scenario in under 20 minutes
    2-3 configurable anomaly scenarios
    Documentation:
    Comprehensive README (setup, usage, architecture)
    User guide with tutorial scenarios
    Technical documentation (API, data models, physics equations)
    Architecture diagrams and system flow
    Code Repository:
    Clean, well-organized GitHub repository
    Unit and integration test suite
    Setup scripts for easy installation
    Example configurations and data
    Final Presentation:
    Live demo of core use cases
    Discussion of architectural tradeoffs observed
    Lessons learned and future directions

11. Future Enhancements (Post‑Capstone)
    User accounts and authentication
    Saved simulations and templates
    Multi-user classroom support
    Advanced anomaly models

Document Status
Current Status: Draft (Proposal‑Safe MVP)
Prepared for: CSC400 — SRS document made based off of SRS template, created by the team, edited for clarity by ChatGPT, Gemini, and Deepseek. Finalized by the team for presentation.
Semester: Spring 2026
