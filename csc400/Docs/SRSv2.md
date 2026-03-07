Software Requirements Specification (SRS)
Project Name: E-Habitat: Interactive Server Room Monitoring Simulator
Client/Sponsor: Self-Proposed
Team Members:
Name
Role/Responsibilities
Email
Logan Caraballo
Project Lead / Backend
caraballol2@southernct.edu
Jared He
Frontend / UI
hej6@southernct.edu
Gavin Paeth
Data, Testing
paethg1@southernct.edu
Document Version: v1.1
Last Updated: 27 Feb 2026

1. Executive Summary
   1.1 Project Overview
   E-Habitat is an interactive educational simulation platform designed to help learners understand distributed systems concepts by comparing centralized and edge-based monitoring architectures in a realistic server room environment. The system simulates thermal, airflow, and humidity dynamics across multiple virtual nodes and visualizes how different monitoring strategies detect anomalies under identical conditions. E-Habitat enables hands-on exploration of architectural tradeoffs without requiring physical infrastructure.
   1.2 Problem Statement
   Students studying distributed systems often encounter abstract concepts such as edge computing, centralized monitoring, latency, and bandwidth tradeoffs without access to realistic experimentation environments. Existing tools are either production-grade monitoring systems that are too complex for educational use or purely theoretical materials that lack experiential learning. This gap limits students’ ability to develop intuition about real-world distributed system behavior. This is why our team must create a new product that bridges this gap, adding personalization to the learning process.
   1.3 Solution Overview
   E-Habitat addresses this gap by providing a controlled, visual, and interactive simulation where centralized and edge monitoring architectures operate simultaneously on the same environmental data. By allowing users to inject anomalies and observe detection latency, bandwidth usage, and system behavior in real time, the platform makes distributed systems principles concrete and observable.
   1.4 Client Context
   Client Organization: Self-Proposed
   This project is self-proposed and intended for use by computer science students, instructors, and self-learners in academic settings. The primary success criteria are educational clarity, ease of setup, and the ability to demonstrate architectural tradeoffs during live demos or guided lab exercises. Requirements and scope were validated against typical distributed systems course objectives and instructor-led demonstration needs.
2. User Research & Personas
   2.1 Research Methods
   Research conducted:

- [ ] Client discovery interviews ([number] conducted)
- [ ] End-user interviews ([number] conducted)
- [ x ] Observation/shadowing
- [ ] Survey ([number] responses)
- [ ] Competitive analysis
- [ x ] Other: Course experience, review of distributed system curriculum, analysis of existing monitoring and simulation tools.
  Key Findings:

1. Visual feedback is a top priority for knowledge retention
2. Experiments must be repeatable
3. Interface must be simple and approachable to ensure a focus on architectural behavior rather than operational complexity.
   2.2 User Personas
   Primary User Persona
   Name & Role: John Doe, Computer Science Student
   Demographics: Upper-level undergraduate or graduate student studying distributed systems and/or related topics. Intermediate technical proficiency.
   Organization Context: School of around ~10,000 students, student, reporting to their professor(s)
   Needs:

- Observe how centralized and edge monitoring differ under the same conditions
- Experiment with anomalies and interpret system behavior
  Pain Points:
- Abstract concepts without hands-on reinforcement
- Lack of accessible simulation tools
  Goals:
- Develop intuition about latency and bandwidth
- Learn how to handle faults and anomalies in the system
  Technology Context: Laptop running a local development environment
  Secondary User Persona
  Name & Role: Jane Doe, Course Instructor
  Demographics: University-level instructor teaching systems courses
  Needs:
- Reliable classroom demonstrations
- Controlled scenarios to illustrate specific concepts
  Pain Points:
- Contemporary software is too complicated to efficiently convey intended concepts
  Goals:
- Reinforce lecture material with visual, repeatable experiments
  Add additional personas if your application serves distinctly different user types.

3. User Stories
   Format
   As a [type of user], I want [some goal] so that [some benefit].
   Must Have (MVP Features)
   These are the features required for your application to deliver core value. Aim for 8-12 user stories.
   Authentication & User Management
   US001: As a new user, I want to create an account so that I can access the system securely.
   Acceptance Criteria:

- [ x ] User can register with email/password
- [ x ] Validation requirement - email must be the proper format
- [ ] Security requirement - e.g., password meets complexity rules
- [ ] Post-registration behavior - e.g., confirmation email sent
- [ x ] Redirect behavior - e.g., user redirected to dashboard
  US002: As a returning user, I want to log in and stay authenticated so that I don't have to re-enter credentials frequently.
  Acceptance Criteria:
- [ ] User can log in with [method]
- [ x ] Session persists until manual logout
- [ x ] User can manually log out
- [ ] Session expires after [duration] of inactivity
      Core Feature: Simulation Control
      US003: As a user, I want to start and stop a simulation so that I can observe environmental behavior in real time.
      Acceptance Criteria:
- Telemetry begins streaming within one second of start
- Simulation runs at one-second time steps
- Real-time updates
- Alerts update user to notable simulation events
  US004: As a user, I want to configure baseline environmental parameters so that I can explore different operating conditions.
  Acceptance Criteria:
- Users can set temperature, airflow, and humidity ranges before simulation start
- Invalid values are rejected with clear feedback
- Parameters can be adjusted in real-time by the user
  Core Feature: Anomaly Interaction
  US005: As a user, I want to inject predefined anomaly scenarios so that I can observe how each architecture responds.
  Acceptance Criteria:
- Thermal spike and HVAC failure scenarios are supported
- Visual indicators show when anomalies occur
- Anomaly alerts will show up in a well-defined area
  Core Feature: Architecture Comparison
  US006: As a user, I want to view centralized and edge monitoring results side by side so that I can compare tradeoffs.
  Acceptance Criteria:
- Both architectures run simultaneously on identical data
- Comparison metrics include detection latency and message volume
- Support for up to 3 nodes running simultaneously in a side-by-side view
  Core Feature: Visualization
  US007: As a user, I want to view real-time telemetry and alerts so that I can interpret system behavior.
  Acceptance Criteria:
- Live charts update with less than 200ms latency
- Alerts appear when anomalies are detected
- Visual aids such as gauges and sliders for accessibility
  Should Have (Post-MVP Enhancements)
  Features to implement if time permits after MVP is complete.
  • User accounts and authentication (tentative)
  • Saved simulations and templates (tentative)
  • Multi-user classroom support
  • Advanced anomaly models
  Could Have (Future Considerations)
  Features documented for future development, not planned for this semester.
  USXXX: [Nice-to-have feature]
- [Brief description]

4. Features & Requirements
   4.1 Core Features 1. Simulation Engine — Simulates thermal, airflow, and humidity dynamics across three virtual nodes at one-second intervals. 2. Dual Monitoring Architectures — Centralized raw-telemetry streaming and edge-based local anomaly detection running concurrently. 3. Anomaly Scenarios — Two predefined anomaly scenarios with manual injection controls. 4. Real-Time Dashboard — Displays telemetry, alerts, and architecture comparison metrics. 5. Educational Comparison Metrics — Detection latency and network message volume for each architecture.
   Aim for 5-8 core features. Each should map to multiple user stories.
   4.2 Technical Requirements
   Authentication & Authorization
   • Authentication method - email/password
   • User profile creation and management
   • Session management (persists until user logs out)
   • Role-based access for students, instructors
   • Password reset and account recovery
   Data Management (CRUD Operations)
   • Create: Users can create nodes with preset configurations
   • Read: Users can see node behavior react to changing environmental parameters
   • Update: Users can modify parameters in presets and active simulations
   • Delete: Users can delete unwanted presets
   Database & Storage
   • Primary Database: SQLite
   • Key Data Entities: User accounts, user-created node presets
   • Users: User authentication details, roles
   • User Accounts: User’s email and password
   • User Presets: User’s previously created node presets
   Simulation Engine
   • The system shall simulate at least three virtual nodes concurrently.
   • The system shall stream telemetry using WebSockets.
   • The system shall compute anomaly scores using a pre-trained Isolation Forest model.
   • The system shall display alerts when anomaly thresholds are exceeded.
   4.3 Non-Functional Requirements
   Performance
   • Dashboard updates shall occur with less than 200ms latency
   • Support for at least three nodes without dropped messages
   Security
   • HTTPS encryption for all data transmission
   • Hashed passwords with industry-standard encryption
   • Input validation
   Usability
   • Interface shall support live demos without prior configuration
   • Core actions shall be accessible within two clicks
   • UI elements should be intentionally placed with simplicity in mind
   • Optimization for dark mode theme
   • All core information should be available at-a-glance
   Reliability
   • System shall run continuously for at least one hour without failure
   • Error messages should be used when appropriate
   • ML engine should avoid hallucinations
5. System Design
   5.1 Technology Stack
   Frontend:

- Languages: TypeScript (typed superset of JavaScript)
- Framework: Next.js, React
- UI Library: Tailwind CSS, Material UI
  Backend:
- Runtime: Python 3.10+, Uvicorn (runtime server)
- Framework: FastAPI
- Authentication Library: Planned
- Validation Library: Pydantic (built into FastAPI)
  Database:
- Database: SQLite (planned)
- ODM/ORM: Planned
  Deployment:
- Hosting Platform: Local
- Process Manager: Local
- Web Server: Nginx (planned)
- SSL Certificate Source: Let’s Encrypt (planned)
  Development Tools:
- Version control: Git + GitHub
- Package Manager: npm, pip
- Environment Management: Node.js runtime, Python virtual environment (venv)
- Testing Tools: pytest
  Third-Party Services:
- Authentication Provider: None
- Email Services: None
- Other: NumPy (library in Python for ML integration)
  5.2 User Interface Design
  Design Principles:
- Desktop-first responsive design
- Minimal clicks to perform core functions
- “At-a-glance” viewing convenience
  Key Screens:

1. Landing/Login Page

- Purpose: Provide users with the option to login
- Key Elements: Primary dashboard, login as button in header
- User Actions: Dashboard to perform primary functions, option to login

2. Dashboard

- Purpose: All functionality intentionally laid out for user convenience
- Key Elements: Nodes, visual aids, sliders (for configurable parameters), alerts feed, status aids
- User Actions: Adjust parameters, view effects in real-time

3. [Core Feature Screen]

- Purpose: [Description]
- Key Elements: [List main UI components]
- User Actions: [What users can do]

4. [Core Feature Screen]

- Purpose: [Description]
- Key Elements: [List main UI components]
- User Actions: [What users can do]

5. Profile/Settings

- Purpose: User account management
- Key Elements: View previously saved presets, change email for login
- User Actions: View presets, change login information, logout
  Include wireframes or mockups: Attach hand-drawn sketches, Figma designs, or other visual representations of key screens.

  5.3 Database Schema
  Entity Relationship Diagram: [Attach ERD or describe relationships]
  Entity: User
  {
  \_id: ObjectId,
  email: String (unique, required),
  passwordHash: String (required), // or googleId for OAuth
  firstName: String (required),
  lastName: String (required),
  role: String (enum: ['admin', 'coordinator', 'user']),
  profilePicture: String (URL, optional),
  createdAt: Date,
  lastLogin: Date,
  isActive: Boolean (default: true)
  }

Entity: [Your Main Entity]
{
\_id: ObjectId,
[field]: [type] (constraints),
[field]: [type] (constraints),
[field]: [type] (constraints),
createdBy: ObjectId (ref: User, required),
createdAt: Date,
updatedAt: Date
}

Entity: [Your Second Entity]
{
\_id: ObjectId,
[field]: [type] (constraints),
[relationship]: ObjectId (ref: [Entity], required),
createdAt: Date
}

Include all main entities with field names, types, constraints (required, unique, enum values), relationships (references), and indexes for performance.
5.4 System Architecture
Architecture Pattern: REST client-server (currently), MVC (planned)
Component Diagram:

Request/Response Flow:

1. User makes HTTP GET request (browser/client)
2. FastAPI (route handler) calls node.step() to advance one timestep
3. Simulation Engine updates state in memory (various user-configurable parameters)
4. FastAPI returns JSON response, UI state updates
   Security Layer:

- Authentication Handling: Planned
- Authentication Enforcement: Planned
- Input Validation: Planned

6. Implementation Plan
   6.1 Development Phases
   Phase 1: Foundation & Setup
   Timeline: Week 0 - Week 4
   Goal: Project setup, authentication working, basic deployment
   Deliverables:

- [ x ] Development environment configured (all team members)
- [ x ] GitHub repository with branching strategy
- [ x ] Extract normal operating ranges from all three datasets
- [ x ] Calculate statistical distributions (mean, variance, percentiles)
- [ x ] Set simulation default parameters to match real-world baselines
- [ ] Application deployed to hosting platform
      Team Responsibilities:
- Logan: Initialize nodes, parameter effects on node behavior
- Jared: Nodes displayed on page, parameters affect node simulation
- Gavin: Process datasets, establish baseline statistics
  Phase 2: Core Feature Development
  Timeline: Week 5 - Week 8
  Goal: Primary features functional
  User Stories Targeted:
- US003: Simulation start/stop
- US004: Environmental parameters adjustable by user
- US005: Anomaly injection
- US006: Node comparison
  Deliverables:
- [ x ] Run simulation with real-world parameters
- [ x ] Compare synthetic output distributions to real data
- [ x ] Tune heat transfer coefficients, cooling rates, and noise levels
- [ x ] Basic UI for primary workflows
- [ x ] Generate 48 hours of synthetic normal operation telemetry
- [ x ] Combine with normal periods extracted from real datasets
- [ x ] Train Isolation Forest on merged normal data
- [ x ] Validate detection on known anomalies from real datasets
  Team Responsibilities:
- Logan: Implement additional parameters, ML initialization
- Jared: Reflect additional parameters on dashboard, addition of alerts feed, ML integration
- Gavin: Establish dataset baseline for ML model, database initialization
  Phase 3: Feature Completion & Integration
  Timeline: Week 9 - Week 12
  Goal: All MVP features complete
  User Stories Targeted:
- US001-US007: All must-have features implemented
- Integration between components
- Error handling and edge cases
  Deliverables:
- [ ] All core features complete and integrated
- [ ] Comprehensive error handling
- [ ] UI/UX refinements based on testing
- [ ] Client feedback incorporated
- [ ] Performance optimization
      Team Responsibilities:
- Logan: Physics engine refinement, ML training continued
- Jared: Integration of additional UI elements, additional ML requirements
- Gavin: Database integration for users, user-configurable presets
  Phase 4: Testing, Polish & Documentation
  Timeline: Week 13 - Week 16
  Goal: Production-ready application with full documentation
  Deliverables:
- [ ] User acceptance testing with client
- [ ] Bug fixes and refinements
- [ ] Accessibility compliance testing
- [ ] Security review
- [ ] Performance optimization
- [ ] User documentation (help guides, FAQ)
- [ ] Technical documentation (README, deployment guide)
- [ ] Fully tested, production-ready application
- [ ] Client sign-off

Phase 1: Foundation (Weeks 1–4) — COMPLETE
Goal: Working single-node simulation with physics engine, ML pipeline, and basic dashboard.
Completed Deliverables
• Development environment and GitHub repository configured for all team members.
• Physics engine fully implemented: thermal, airflow, and humidity models.
• Real datasets (MIT Intel Lab, DOE, Kaggle HVAC) downloaded and processed; statistical summaries extracted.
• Physics parameters calibrated against real-world data distributions.
• Single virtual node prototype implemented with anomaly detection hooks.
• Isolation Forest model trained on synthetic calibrated telemetry and serialized as .pkl.
• FastAPI REST backend established with /telemetry/step endpoint.
• Next.js dashboard displaying live telemetry with sub-200ms update latency.
• Thermal spike anomaly injection implemented and verified end-to-end.
Sprint 1 Deliverable: Achieved. Single-node simulation streaming telemetry, detecting injected thermal anomaly, and displaying on dashboard.
Phase 2: Multi-Node & Architecture Comparison (Weeks 5–8) — PARTIALLY COMPLETE
Goal: 3-node system with both monitoring architectures operational and comparison metrics visible.
Completed Deliverables
• HVAC failure anomaly scenario implemented in the physics engine.
• Architecture comparison panel added to dashboard (detection latency, message volume).
• Backend alert routing and aggregation logic implemented.
• Dashboard UI expanded for multi-node telemetry panels.
• Performance optimization: chart history capped at 5 minutes, updates throttled to 1–2 per second.
• README drafted with setup instructions, architecture diagram, and usage guide.
In Progress / Delayed
• WebSocket streaming: currently implemented as REST polling (/telemetry/step). Migration to persistent WebSocket connection is the top Phase 3 priority.
• Multi-node backend: api.py initializes one VirtualNode instance. Three-node multiplexing targeted for Phase 3 Week 9.
• SQLite database: system operates in-memory. Schema design and implementation delayed to Phase 3.
• Authentication: no auth logic present in current codebase. Targeted for Phase 3 Weeks 10–11.
Sprint 2 Deliverable: Partially achieved. Architecture comparison panel is operational. Full 3-node WebSocket demo deferred to Phase 3.
Phase 3: Core Completion & Infrastructure (Weeks 9–12)
Goal: Close all Must Have gaps (WebSockets, 3 nodes, authentication, SQLite). Complete and test all MVP user stories.
Week 9 — Infrastructure Sprint
• Logan: Migrate /telemetry/step REST endpoint to persistent WebSocket connection. Update message schema to preserve node identity across multiplexed streams.
• Logan: Expand backend to initialize and run three VirtualNode instances concurrently. Validate synchronization and consistent timing.
• Gavin: Design and implement SQLite schema for user accounts and node presets. Initialize database layer with migration scripts.
• Jared: Update frontend WebSocket client to handle multi-node streams. Confirm dashboard renders all three node panels simultaneously.
Week 10 — Authentication & Presets
• Logan: Implement email/password authentication endpoints (register, login, logout). Add session middleware to FastAPI.
• Gavin: Implement CRUD operations for node presets backed by SQLite. Connect preset management to user session.
• Jared: Build login/register UI screens. Integrate session persistence and protected routes into Next.js frontend. Add preset management to profile/settings screen.
Week 11 — Third Anomaly Scenario & Integration Testing
• Logan: Implement a third anomaly scenario (airflow blockage) if timeline permits. Confirm cascading physics effects across nodes.
• All: Full system integration testing under 3-node load. Address race conditions, timing issues, or UI lag identified during testing.
• All: End-to-end 60-minute continuous runtime validation.
Week 12 — Phase 3 Stabilization
• All: Bug fixes from integration testing.
• Jared: Dashboard UI refinements based on internal review — layout clarity, labeling, and educational cues.
• All: Documentation updates — README, API reference, architecture diagrams.
Phase 3 Deliverable: All Must Have user stories (US001–US007) fully implemented and integration-tested. Three-node WebSocket simulation with authentication and SQLite persistence operational.
Phase 4: Testing, Polish & Finalization (Weeks 13–16)
Goal: Production-ready demo system with comprehensive testing, external user validation, and complete documentation.
Week 13 — External User Testing
• Recruit 2–3 external testers (classmates not on the team).
• Conduct observed usability sessions: install, run simulation, inject anomaly, interpret metrics.
• Document usability issues, confusion points, and documentation gaps.
• Prioritize fix list from tester feedback.
Week 14 — Feedback Integration & Security Review
• All: Address high-priority usability issues from Week 13 testing.
• Logan: Security review — authentication flow, input validation, session handling.
• Gavin: Finalize unit test suite for physics engine and anomaly detection. Achieve meaningful coverage on all critical paths.
• Jared: Accessibility review — keyboard navigation, contrast, label clarity.
• All: Documentation improvements based on tester feedback.
Week 15 — Demo Preparation & Final Testing
• All: Final integration testing under demo conditions. Confirm zero crashes and consistent anomaly detection across all scenarios.
• All: Demo rehearsal — script complete demonstration sequence highlighting architectural tradeoffs and performance metrics.
• All: Prepare presentation materials: slides covering system design, validation process, tradeoffs observed, and lessons learned.
• All: Code cleanup — remove dead code, verify docstrings and comments are complete, finalize repository structure.
Week 16 — Final Demo & Submission
• Deliver live demonstration showing anomaly injection and architecture comparison in real time.
• Submit final SRS, source code, documentation, and presentation materials.
• Post-mortem review: document lessons learned and future enhancement roadmap.
Phase 4 Deliverable: Complete, tested, documented system demonstrated live. All success criteria met. Repository in final submission state.

6.2 Anomaly Detection Pipeline (Replaced Client Engagement Schedule)
Training (Offline): 1. Generate baseline telemetry using physics engine with real-data parameters 2. Extract sliding-window features (10-second windows) 3. Train Isolation Forest on normal operation only 4. Save model as .pkl artifact for deployment
Inference (Real-Time During Simulation): 1. Nodes collect telemetry in sliding windows 2. Extract features (mean, variance, rate-of-change) 3. Run Isolation Forest prediction 4. If anomaly score exceeds threshold → trigger alert 5. Transmit alert (edge) or raw data (centralized) to backend
Why Isolation Forest:
• Unsupervised: doesn't require labeled anomalies
• Fast: suitable for real-time edge inference
• Interpretable: anomaly scores are understandable
• Proven: widely used in production anomaly detection
Limitations Acknowledged:
• Detects deviations, doesn't predict future events
• Threshold tuning required for different scenarios
• May produce false positives on rare-but-normal events
• More sophisticated models (LSTM, Autoencoder) deferred to post-capstone
6.3 Testing Strategy
Testing Approaches: 1. Manual Testing

- Test all user workflows before each milestone
- Cross-browser testing (Chrome, Firefox, Safari, Edge)
- Mobile responsiveness testing
- Client-specific scenario testing 2. User Acceptance Testing (UAT)
- Testing sessions using external systems and/or users (if possible) in Weeks 13-15
- Document feedback and prioritize fixes 3. Security Testing
- Authentication flow testing
- Authorization/access control verification
- Input validation testing
  Success Criteria:
- [ ] All must-have user stories meet acceptance criteria
- [ ] No critical bugs in core workflows
- [ ] Performance meets non-functional requirements
- [ ] Client approves final product
      6.4 Deployment Strategy
      Environments:
- Development: Local machines, test database
- Production: Google Cloud Platform (if credits are granted), production database
  Deployment Process:

1. Development: Code and test locally
2. Version control: Commit to feature branch
3. Code review: Pull request and team review
4. Merge: To main branch after approval
5. Deploy: GCP deployment SOP
6. Verify: Test production deployment
   Rollback Plan:

- Keep previous version tagged in Git
- Database backup before each deployment
- Rollback procedure documented

7. Risk Assessment
   Technical Risks
   Risk 1: Physics Engine Complexity Exceeds Timeline

- Impact: High - Core simulation doesn't work realistically, undermines entire project
- Likelihood: Medium
- Mitigation:
- Start with simplified thermal-only model in Week 1
- Validate against real data early (Week 2)
- If complex physics takes >3 weeks, simplify models using lookup tables instead of differentials
- Contingency: Use temperature only; defer humidity/airflow to post-capstone
  Risk 2: WebSocket Performance Issues at Scale
- Impact: Low - Dashboard lags or drops messages with multiple nodes
- Likelihood: Medium
- Mitigation:
- Test with 3 nodes early (Week 5)
- Implement message batching if needed
- Use existing WebSocket libraries (avoid custom protocols)
- Contingency: Reduce to 2 nodes for demo, or use HTTP polling instead of WebSockets
  Risk 3: Real-Time Dashboard Responsiveness
- Impact: Low - Charts stutter, poor user experience
- Likelihood: Medium
- Mitigation:
- Use proven charting library (Recharts) optimized for real-time
- Limit chart history to last 5 minutes
- Throttle updates to 1-2 per second
- Contingency: Dashboard shows delayed data (5-10 second lag acceptable), or snapshot updates
  Risk 4: SQLite Performance for Time-Series Data
- Impact: Medium - Query slowdowns, storage bottlenecks
- Likelihood: Low
- Mitigation:
- Keep simulation duration short (<1 hour)
- Index timestamp columns
- Batch inserts
- Contingency: Write-only database during simulation, or switch to in-memory storage
  Risk 5: Integration Challenges Between Components
- Impact: High - Components work separately but fail together
- Likelihood: Low
- Mitigation:
- Integration testing starting Week 4, frequent end-to-end testing
- Contingency: Simplify interfaces, use polling instead of real-time where needed
  Risk 6: Anomaly Detection Produces Too Many False Positives
- Impact: High - Demo shows useless alerts, undermines educational value
- Likelihood: Low
- Mitigation:
- Tune Isolation Forest threshold during validation (Week 4)
- Contingency: Use simple rule-based detection (threshold crossings) instead of ML
  Project Risks
  Risk 1: Scope creep - initial plans exceed timeline
  Impact: High
  Likelihood: Medium
  Mitigation:
  • Document clear scope in SRS with client sign-off
  • Use "Should Have" and "Could Have" for stretch features
  • Weekly communication about progress vs. Scope
  • Document future enhancements for post-semester
  Risk 2: Team member availability
  Impact: Medium - Work falls behind schedule
  Likelihood: High
  Mitigation:
  • Clear task assignments with deadlines
  • Weekly standups/meetings
  • Parallel workstreams, cross-training different components
  Risk 3: Lack of funds
  Impact: High - Will not be able to host on GCP VM without credits, forced local operations
  Likelihood: High
  Mitigation:
  • Winning the lottery
  • Finding large suitcase of money on side of road (or elsewhere)
  • Otherwise sudden influx of cash

8. Success Metrics
   User Metrics
   • Metric: User can view all relevant data at-a-glance
   • Target: 80% of users report adequate information presented on dashboard; <10% users complain about excessive visual clutter. <1% users complain about lack of information
   • Measurement: Blind test with unsuspecting users (no chance for bias)
   Technical Metrics
   • Simulation load time: <10 seconds
   • Uptime during testing: >60 minutes with no crash
   • Zero critical security vulnerabilities
   • Anomalies detected in both architectures during demos
   • 2-3 configurable anomalies
   Client Success Criteria
   Document specific success criteria defined with your client:

- [e.g., "System reduces admin time by 50% vs. current process"]
- [e.g., "100% of volunteer hours tracked accurately"]
- [e.g., "Generate compliance reports in under 5 minutes"]
  Team Metrics
  • All phase milestones completed on schedule
  • All team members contribute to codebase
  • Client attends and approves major presentations
  Documentation:
  • Comprehensive README (setup, usage, architecture)
  • User guide with tutorial scenarios
  • Technical documentation (API, data models, physics equations)
  • Architecture diagrams and system flow
  • Installation requirements (.txt) in directory for easy installation
  Code Repository:
  • Clean, well-organized GitHub repository
  • Unit and integration test suite
  • Setup scripts for easy installation
  • Example configurations and data
  Final Presentation:
  • Live demo of core use cases
  • Discussion of architectural tradeoffs observed
  • Lessons learned and future directions

9. Appendix
   A. Glossary
   Define technical terms, acronyms, and domain-specific terminology:
   • ML: Machine Learning - Process of training algorithms to make predictions and/or decisions based on learned data and pattern recognition.
   • ORM/ODM: Object-Relational/Document Mapping - Allows for interaction with a relational database using objects in a programming language (instead of raw SQL queries)
   • MVP: Minimum Viable Product - core features needed for launch
   • CRUD: Create, Read, Update, Delete - basic database operations
   • UAT: User Acceptance Testing - testing with real users
   • WebSocket: A persistent, full-duplex communication protocol enabling real-time data streaming between client and server.
   • Isolation Forest: An unsupervised machine learning algorithm for anomaly detection based on random partitioning of feature space.
   • Centralized Computing: A centralized architecture where data processing occurs in one central location (usually a cloud data center).
   • Edge Computing: A distributed architecture where data processing occurs locally at or near the data source, rather than in a central server.
   B. References
   • [Client documentation or requirements]
   • [User research artifacts]
   • [Technical documentation consulted]
   • [Third-party API documentation]
   C. Change Log
   Date
   Version
   Changes
   Author
   01 Feb 2026
   v1.0
   MVP SRS draft
   Logan, Jared, Gavin
   27 Feb 2026
   v1.1
   SRS modified according to professor’s comments
   Logan,
   Jared,
   Gavin
   01 Mar 2026
   v1.2
   Corrected project timeline to 16 weeks (4 phases); expanded Phases 3 and 4 with full week-by-week detail; updated Sprint 3 deliverable; added Phase 4 Testing & Finalization section; minor scope clarifications throughout
   Logan, Jared, Gavin
   [Date]
   v2.0
   Final SRS after presentation feedback
   [Team]
   Document Status
   Current Status: Draft / Under Review / Approved
   Approval:

- [ x ] Team approval (all members reviewed)
- [ x ] Client approval (requirements confirmed)
- [ x ] Instructor feedback incorporated

Prepared by: Logan, Jared, Gavin
Course: CSC400 - Computer Science Project Seminar
Semester: Spring 2026
