**DESIGN AND IMPLEMENTATION OF A DISTANCE-RISK-AWARE DYNAMIC PRICING MODEL FOR CITY TRANSPORTATION SERVICES**

**BY**

**CHUKWUDIFU GOLDEN IFEANYICHUKWU**

**20211258722**

**&**

**OBIKUDU CHIGOZIE JEFFREY**

**20222314712**

**A PROJECT PRESENTED TO THE DEPARTMENT OF SOFTWARE ENGINEERING, SCHOOL OF INFORMATION AND COMMUNICATION TECHNOLOGY, FEDERAL UNIVERSITY OF TECHNOLOGY OWERRI**

**IN PARTIAL FULFILLMENT FOR THE AWARD OF BACHELOR OF TECHNOLOGY (B. TECH) IN SOFTWARE ENGINEERING**

**AUGUST 2026**

# CERTIFICATION

I certify that this project “design and implementation of a distance-risk-aware dynamic pricing model for city transportation services” was carried out by Chukwudifu Golden Ifeanyichukwu

(20211258722) & Obikudu Chigozie Jeffrey (20222314712) in partial fulfilment for the award of the degree of B-Tech in Software Engineering, of the Federal University of Technology, Owerri.

Engr. Dr. A. I. Erike Date

(Project Supervisor)

Dr. C.O. Ikerionwu Date

(HOD, SOE)

Prof. U. F. Eze. Date

(Dean, SICT)

(External Examiner) Date

# DEDICATION

We dedicate this work to our biological and church family for their unwavering patience, endless encouragement, and constant love throughout this journey. This work would not have been possible without their belief in us, the resources made available for our utilization, and the home that sustained us. You are our greatest inspiration and most important achievement.

# ACKNOWLEDGEMENT

I wish to express my deepest gratitude to the individuals whose guidance and support were instrumental in the completion of this research.

My sincere thanks go to my project supervisor, **Engr. Dr. A. I. Erike**, for his invaluable intellectual mentorship, insightful critiques, and unwavering support from the initial conceptualization to the final draft of this work.

I am also indebted to the Head of Department, **Dr. C.O. Ikerionwu**, for providing the necessary administrative structure and environment that made this study possible, and to my course advisor, **Dr. Mrs. Elei Florence**, for her consistent counsel and guidance throughout my academic program.

Finally, I extend my appreciation to all the lecturers and laboratory technologists of the Department for their foundational instruction, resource support, and dedication to academic excellence.

# ABSTRACT

Urban transportation systems are undergoing a significant transformation, yet current pricing models remain inadequate as they often ignore route-level risks factors that influences transportation. This study presents the design and implementation of a Distance-Risk-Aware Dynamic Pricing Model aimed at addressing the shortcomings of traditional static or purely distance-based fares. The core problem identified is that existing schemes fail to account for variable traffic, fluctuating demand, and heterogeneous risk profiles across city zones, leading to systematic driver under-compensation and opaque pricing for passengers. The proposed model integrates a multi-variable pricing framework that combines geospatial distance computation, a time-weighted demand multiplier, and a unique Route Risk Coefficient derived from accident statistics, road quality indices, and security data. To support this model, a microservices-based software architecture is designed, consisting of four primary services: Routing, Risk Assessment, Demand Intelligence, and a Pricing Engine.

A working prototype of the architecture was implemented as a REST API (FastAPI) backend with a Next.js web frontend, backed by a PostgreSQL database, and validated with an automated unit-test suite. The prototype confirms that the core Fare Function, F = B + αD + βDR + γM, and its Route Risk Coefficient and Demand Multiplier sub-models, can be computed deterministically and returned to a client as an auditable, component-logged quotation. Several elements of the originally proposed architecture — including a PostGIS-backed risk store, an H3 hexagonal demand grid, and Redis-based caching and pub/sub — remain future work pending real accident, road-quality, and demand data partnerships, and are reported honestly as such rather than as completed features. Implementation of this model promises improved fairness for drivers navigating challenging urban corridors and enhanced transparency for passengers through auditable, decomposable fare components. Ultimately, the study demonstrates that integrating risk-awareness into dynamic pricing is a practically feasible advancement for next-generation city transportation platforms, particularly within the context of African urban infrastructure.

# TABLE OF CONTENTS

[CERTIFICATION [ii](#certification)](#certification)

[DEDICATION [iii](#dedication)](#dedication)

[ACKNOWLEDGEMENT [iv](#acknowledgement)](#acknowledgement)

[ABSTRACT [v](#abstract)](#abstract)

[TABLE OF CONTENTS [vi](#_Toc239457579)](#_Toc239457579)

[LIST OF TABLES [viii](#list-of-tables)](#list-of-tables)

[LIST OF FIGURES [ix](#list-of-figures)](#list-of-figures)

[LIST OF ABBREVIATIONS [x](#list-of-abbreviations)](#list-of-abbreviations)

[CHAPTER ONE [1](#chapter-one)](#chapter-one)

[1.1 Background to the study [1](#background-to-the-study)](#background-to-the-study)

[1.2 Problem Statement [2](#problem-statement)](#problem-statement)

[1.3 Objectives [3](#objectives)](#objectives)

[1.4 Research Questions [3](#research-questions)](#research-questions)

[1.5 Scope of the Study [4](#scope-of-the-study)](#scope-of-the-study)

[1.6 Limitations of the Study [4](#limitations-of-the-study)](#limitations-of-the-study)

[1.7 Significance of the Study [5](#significance-of-the-study)](#significance-of-the-study)

[1.8 Definition of Terms [5](#definition-of-terms)](#definition-of-terms)

[CHAPTER TWO [8](#chapter-two)](#chapter-two)

[2.1 Conceptual Framework [8](#conceptual-framework)](#conceptual-framework)

[**2.1.1 Input Variables** [8](#input-variables)](#input-variables)

[**2.1.2 Process Variable: Fare Function** [9](#process-variable-fare-function)](#process-variable-fare-function)

[**2.1.3 Output Variable: Final, Transparent Fare** [10](#output-variable-final-transparent-fare)](#output-variable-final-transparent-fare)

[2.2 Theoretical Framework [10](#theoretical-framework)](#theoretical-framework)

[2.3 Empirical Framework [11](#empirical-framework)](#empirical-framework)

[**2.3.1 Dynamic Pricing and Equity in Ride-Hailing** [11](#dynamic-pricing-and-equity-in-ride-hailing)](#dynamic-pricing-and-equity-in-ride-hailing)

[**2.3.2 Route Risk Prediction** [11](#route-risk-prediction)](#route-risk-prediction)

[**2.3.3 Geospatial Routing and Route Optimisation** [12](#geospatial-routing-and-route-optimisation)](#geospatial-routing-and-route-optimisation)

[CHAPTER THREE [14](#chapter-three)](#chapter-three)

[3.1 Methodology Adopted [14](#methodology-adopted)](#methodology-adopted)

[CHAPTER FOUR [17](#chapter-four)](#chapter-four)

[4.1 System Architecture [17](#system-architecture)](#system-architecture)

[4.2 Tools and Technologies Used [18](#tools-and-technologies-used)](#tools-and-technologies-used)

[4.3 Database Design [18](#database-design)](#database-design)

[4.4 Pricing, Risk, and Demand Model Implementation [19](#pricing-risk-and-demand-model-implementation)](#pricing-risk-and-demand-model-implementation)

[4.5 Use Case Design [21](#use-case-design)](#use-case-design)

[4.6 API Design [22](#api-design)](#api-design)

[4.7 User Interface Design [22](#user-interface-design)](#user-interface-design)

[4.8 Benefits of the Implemented System [23](#benefits-of-the-implemented-system)](#benefits-of-the-implemented-system)

[4.9 Testing [23](#testing)](#testing)

[4.10 System Documentation Summary [24](#system-documentation-summary)](#system-documentation-summary)

[CHAPTER FIVE [26](#_Toc239457615)](#_Toc239457615)

[5.1 Summary of Findings [26](#_Toc239457616)](#_Toc239457616)

[5.2 Conclusion [26](#_Toc239457617)](#_Toc239457617)

[5.3 Recommendations [27](#_Toc239457618)](#_Toc239457618)

[5.4 Contribution to Knowledge [28](#_Toc239457619)](#_Toc239457619)

[5.5 Future Work [28](#_Toc239457620)](#_Toc239457620)

[LIST OF REFERENCES [30](#list-of-references)](#list-of-references)

# LIST OF TABLES

Table 1: Comparison of Dynamic Pricing Approaches 5

Table 2: Risk Classification Matrix for City Zones 11

Table 3: Benefits of the Proposed Pricing Model 11

Table 4: Limitations of the Proposed Pricing Model 12

# LIST OF FIGURES

Figure 1: System Architecture 9

Figure 2: Use Case Diagram for Pricing Engine 10

# LIST OF ABBREVIATIONS

API: Application Programming Interface

FRSC: Federal Road Safety Corps (of Nigeria)

H3: Uber’s Hexagonal Hierarchical Spatial Index

HTTPS: Hypertext Transfer Protocol Secure

NBRRI: Nigerian Building and Road Research Institute

OSM: OpenStreetMap

OSRM: Open Source Routing Machine

REST / RESTful: Representational State Transfer

# CHAPTER ONE

**INTRODUCTION**

## 1.1 Background to the study

Urban ride-hailing and city transportation systems worldwide have undergone significant transformation driven by the rapid rising of ride-hailing platforms, mobility services, and smart city infrastructure. At the heart of this innovation lies the challenge of pricing, how to assign fares that are simultaneously fair to the passenger, financially sustainable for the service provider, and reflective of the true cost and risk of each trip. Traditional flat-rate or simple distance-based pricing models are increasingly inadequate in modern city environments that exhibit highly variable traffic congestion, fluctuating demand, heterogeneous risk profiles across zones, and dynamic operational costs (Cachon et al., 2015).

The rise of platforms such as Uber, Bolt, InDrive, and government-owned city bus services has placed enormous pressure on transportation pricing to evolve beyond static models into dynamic pricing models. The fare logic behind every one of them is the same; a base fee, added to a rate multiplied by distance, added to a rate multiplied by estimated time, occasionally adjusted upward when demand temporarily surpasses the number of available drivers.

Dynamic pricing, sometimes called surge pricing, gained attention both as a practical solution and as a subject of academic inquiry (Chen & Sheldon, 2015).

The concept of dynamic pricing in transportation is rooted in the economic principle of demand elasticity, wherein prices adjust in real-time to balance supply and demand (Yan et al., 2020). In city transportation services, the factors that affect the appropriate price of a ride go beyond mere origin-to-destination distance. Traffic conditions, accident-prone corridors, flood, and neighbourhood safety indices all contribute to the operational risk and cost borne by the driver and the platform. Yet most pricing engines deployed by commercial ride-hailing companies in developing and even developed economies treat these factors superficially or ignore them entirely.

In Nigerian cities such as Lagos, Port Harcourt, and Owerri, the inadequacy of current pricing models is especially pronounced. Road infrastructure quality varies sharply between districts; certain routes through high-density or flood-prone neighbourhoods impose significantly higher vehicle wear and driver risk than routes of similar distances in well-maintained zones. (Acheampong, 2021), in a study of ride-hailing safety and security in an African city context, documented that fare pricing practices perceived as non-transparent were a primary source of conflict between drivers and passengers, and that route-specific risk factors—including neighbourhood safety and road condition—were systematically ignored by existing pricing algorithms. A distance-risk-aware dynamic pricing model that captures these realities would result in fairer pricing for drivers, better revenue management for operators, and an improved passenger experience through transparent, explainable fare structures.

However, the existing implementations either rely purely on demand-supply ratio adjustments or use simple distance multipliers without accounting for route-level risk factors such as accident frequency, road condition indices, or crime statistics along the route. The proposed model integrates both distance computation—via mapping APIs and geospatial algorithms—and a risk assessment layer derived from publicly available urban data, creating a composite pricing function that is more equitable, accurate and fair to all the involved parties.

This project presents the design and implementation of a Distance-Risk-Aware Dynamic Pricing Model that addresses these shortcomings through a data-driven, multi-variable pricing framework.

## 1.2 Problem Statement

The fundamental problem addressed by this Project report is the inadequacy of existing pricing models in city transportation services to account for the full spectrum of factors that determine the true cost of a trip. Many existing transport and ride-hailing systems primarily focus on providing the shortest or fastest routes while paying little attention to the level of risk associated with different routes or travel distances. Factors such as accident-prone roads, high-crime areas, poor road conditions, traffic congestion, environmental disasters (e.g floods), and adverse weather conditions can significantly increase the risk faced by commuters.

These deficiencies have concrete negative consequences. Drivers in high-risk zones are systematically under-compensated, contributing to driver attrition and service unavailability in those areas (Acheampong, 2021). Operators cannot accurately estimate costs or optimise fleet deployment when pricing is decoupled from real operational conditions. Passengers, particularly in low-income urban areas, are exposed to unpredictable surge prices during emergencies when their need is greatest and their ability to pay is most constrained. Regulatory bodies struggle to evaluate fairness and intervene appropriately when pricing algorithms are opaque.

Although several navigation and transport applications provide real-time traffic updates and estimated travel times, many do not integrate multiple risk factors into route selection and travel recommendations. This creates a gap in providing users with transport options that consider both distance and safety.

Therefore, there is a need to develop a distance-risk-aware dynamic pricing model that evaluates travel routes based on distance as well as potential risk factors. Such a system will assist users in making more informed travel decisions by recommending routes that strike a balance between efficiency and safety, thereby improving the overall transportation experience.

## 1.3 Objectives

The primary objective of this project is to design and implement a Distance-Risk-Aware Dynamic Pricing Model for city transportation services. The specific objectives are too:

1.  Carry out a research survey of existing transportation pricing models.

2.  Design a composite Route Risk Coefficient that quantifies accident history, road-surface condition, and route-level security risk for any given route segment.

3.  Design a composite dynamic pricing function that integrates the distance, route risk, and a demand multiplier to produce a fair and transparent fare.

4.  Implement the pricing model as a set of cooperating microservices — a Routing Service, a Risk Assessment Service, a Demand Intelligence Service, and an orchestrating Pricing Engine Service

5.  Evaluate the system against existing pricing approaches using simulation data, demonstrating improvements in users’ travel experience, driver satisfaction, and operational efficiency.

## 1.4 Research Questions

This study seeks to address the following research questions:

**Primary research question:** Can we design and implement a city transportation system that integrates risk-awareness and distance to calculate transportation fare?

**Secondary research questions:**

**RQ1:** What transportation models exist?

**RQ2:** Which factors can be used to determine the route risk?

**RQ3:** How can distance, risk and demand be combined into a fare?

**RQ4:** What architecture can support the model?

**RQ5:** How does the proposed model compare with conventional pricing?

## 1.5 Scope of the Study

This study focuses on the design and implementation of a Distance-Risk-Aware Dynamic Pricing Model for city transportation services. The system will use the passenger's pickup location and destination to determine the travel route, distance, and estimated travel time. It will also assess route risk using factors such as accident incidence, environmental hazards, and security-related incidents.

The system will integrate distance, travel time, route risk, passenger demand, and driver availability to calculate an estimated transportation fare. It will provide a risk-adjusted fare and may present alternative route information where applicable.

The study is limited to the development and evaluation of a software-based prototype using available mapping, transportation, and risk-related data. It will not cover nationwide deployment, physical traffic-monitoring infrastructure, autonomous vehicle control, real-time emergency response, or transportation infrastructure development.

## 1.6 Limitations of the Study

This study is subject to several limitations that may affect the implementation and performance of the proposed Distance-Risk-Aware Dynamic Pricing Model.

1.  Access to verified, city-wide, real-time accident and road-condition datasets from Nigerian road agencies was not available within the timeframe of this project; simulated data from students living in FUTO using Google form quesstionaire was used instead.

2.  The project is developed as a prototype to demonstrate the concept of integrating distance and risk into route planning. As such, it does not provide nationwide coverage or support every road network and transportation service.

3.  In addition, the system considers selected risk factors such as traffic congestion, accident-prone roads, poor road conditions, and high-risk locations. Other factors, including weather changes, road construction, emergency incidents, and individual driver behavior, are beyond the scope of this study and may influence travel safety.

Despite these limitations, the proposed system provides a practical framework for incorporating both distance and risk into transportation route planning and serves as a foundation for future research and development in intelligent transportation systems.

## 1.7 Significance of the Study

This significance of this study lies in its contribution to improving transportation safety and transparency through the integration of both distance and risk factors. The following stakeholders will benefit from the results of this project.

Commuters will be able to identify routes that minimize exposure to potential risks such as traffic congestion, accidents, poor road conditions, and high-risk areas.

Passengers/users will gain the capacity to make safer and more efficient travel decisions.**  
**Transport service providers and ride-hailing operators can also benefit from the system by using its route recommendations to improve service quality, enhance passenger safety, reduce travel delays, and optimize operational efficiency.

For government agencies, road safety authorities, and urban planners, the findings of this study may provide valuable insights into how risk-aware technologies can support transportation planning, traffic management, and road safety initiatives.

Academically, this study contributes to the field of Intelligent Transportation Systems by extending existing route planning approaches to incorporate risk assessment alongside distance. It also serves as a useful reference for researchers and students interested in transportation systems, geographic information systems, route optimization, and software engineering.

Finally, the study provides a foundation for future research aimed at developing more advanced transportation systems capable of integrating additional factors such as weather conditions, real-time emergency events, crime statistics, and machine learning techniques for predictive route optimization.

## 1.8 Definition of Terms

1.  **Dynamic Pricing:** A pricing strategy in which transportation fares are automatically adjusted algorithmically in response to changing factors such as travel distance, traffic conditions, demand, and route risk.

2.  **Distance:** The measurable length between a passenger's pickup location and destination, usually expressed in kilometres (km), which serves as a primary factor in calculating transportation fares.

3.  **Risk:** The degree of potential danger or uncertainty associated with a travel route. In this study, risk includes factors such as traffic congestion, accident-prone roads, poor road conditions, flooding, and high-crime areas that may affect the cost of transportation.

4.  **Distance-Risk-Aware Dynamic Pricing Model:** A computational model that determines transportation fares by considering both the travel distance and the level of risk associated with the selected route, thereby producing fairer and more realistic pricing.

5.  **City Transportation Services:** Transportation services that operate within urban areas to move passengers from one location to another. Examples include taxis, ride-hailing services, shuttle services, and commercial buses.

6.  **Transportation Fare:** The amount charged to a passenger for a transportation service based on predefined pricing parameters.

7.  **Pricing Model:** A mathematical or computational framework used to determine the cost of a transportation service by evaluating one or more influencing factors.

8.  **Route Risk Assessment:** The process of identifying and evaluating the level of risk associated with a travel route before determining the transportation fare.

9.  **Route Risk Coefficient (R):** A composite, weighted numerical score representing the accident, infrastructure, and security risk associated with a given route.

10. **Demand Multiplier (M):** A bounded scaling factor applied to the fare in response to the ratio of ride requests to available driver supply in a given zone.

11. **Travel Distance:** The total length of the route between the pickup point and the destination used in fare computation.

12. **Travel Time:** The estimated duration required to complete a journey under prevailing traffic conditions.

13. **Geographic Information System (GIS):** A computer-based system used to capture, manage, analyze, and display geographical data for route analysis and transportation planning.

14. **API Gateway:** A single entry point that routes client requests to the appropriate backend microservice and enforces cross-cutting concerns such as authentication and rate-limiting

15. **Real-Time Traffic Data:** Up-to-date information on road conditions, traffic flow, accidents, road closures, and other events that may influence transportation pricing.

16. **Algorithm:** A sequence of logical steps or mathematical procedures used by the system to calculate transportation fares based on distance and risk factors.

17. **Ride-Hailing Service:** A technology-enabled transportation service that allows passengers to request rides through a mobile or web application while fares are determined using predefined pricing mechanisms.

18. **City Transportation System:** The network of roads, vehicles, infrastructure, and transportation services that facilitate the movement of people within an urban environment.

# CHAPTER TWO

**LITERATURE REVIEW**

## 2.1 Conceptual Framework

The central concept underlying this study is that a ride-hailing fare should be a transparent function of three observable inputs — trip distance, route risk, and prevailing demand — rather than distance and demand alone. Figure 2.1 presents the conceptual schematic of the proposed model. Distance is obtained from the Routing Service; route risk is obtained from the Risk Assessment Service, which aggregates historical accident data, road-surface condition, and security indicators into a single coefficient; and the demand multiplier is obtained from the Demand Intelligence Service, which tracks the ratio of ride requests to available drivers within a geographics cell over a short time window. These three inputs are combined by the Pricing Engine Service into a single, auditable fare.

![](media/image1.png)

**Figure 2.1: Conceptual Framework of the Distance-Risk-Aware Dynamic Pricing Model**

The remainder of this section takes each of these variables in turn, defines it precisely, explains how it is measured or estimated, and clarifies the role it plays inside the pricing function that is developed in full in Chapter Four.

### **2.1.1 Input Variables**

1.  **Distance (D) — Routing Service**

> D is the trip distance in kilometres, obtained through shortest-path computation on the OpenStreetMap road network. Graph-based routing techniques such as Contraction Hierarchies and Transit Node Routing make it possible to compute this distance in milliseconds even at city scale (Bast et al., 2016), making D a reliable and low-latency input to the pricing model.

2.  **Route Risk (R) — Risk Assessment Service**

> R is a dimensionless index in the range \[0, 1\] representing the composite risk of a given route, calculated as R = w₁R_acc + w₂R_road + w₃R_sec, where R_acc, R_road, and R_sec are the normalised accident-frequency, road-quality, and security sub-indices, and w₁–w₃ are weights summing to 1.0. The inclusion of road quality as a risk determinant is supported by Lee, Nam, and Abdel-Aty (2015), who found pavement surface condition to be a significant predictor of crash severity. Acheampong (2021) further established that route-specific risk factors such as neighbourhood safety are routinely ignored by existing ride-hailing pricing algorithms, motivating R as a distinct input variable rather than an implicit cost.

3.  **Demand Multiplier (M) — Demand Intelligence Service**

> M is a real-time signal in the range \[1.0, 2.5\], computed as M = min(1 + λ(Req/Sup − 1), M_cap), where Req and Sup are active trip requests and available drivers in a zone. Dynamic, demand-responsive pricing of this kind has been shown to improve driver–passenger matching and reduce wait times (Cachon, Daniels, & Lobel, 2017) and to draw more drivers into the platform during high-demand periods (Chen, 2016; Hall & Krueger, 2018). The multiplier's configurable cap (M_cap) operationalises the equity safeguard proposed by Lokhandwala and Cai (2018), preventing unconstrained surge pricing during emergencies.

### **2.1.2 Process Variable: Fare Function**

The three inputs are integrated by the Pricing Engine Service using the composite Fare Function:

F = B + ( α × D) + ( β × D × R) + ( ϒ × M )

where B is the fixed base fare and α, β, and γ are calibration coefficients for the distance rate, risk premium, and demand sensitivity respectively. Combining distance, risk, and demand into a single multi-criteria function follows the approach of He, Wang, Lin, and Tang (2018), who modelled taxi-hailing fares as a function of several interacting cost and compensation factors rather than distance alone. The βDR term is the model's core innovation: it scales the risk premium by distance, ensuring longer trips through high-risk corridors attract a proportionally higher premium than short ones.

### **2.1.3 Output Variable: Final, Transparent Fare**

The output of the process is F, the final fare returned to the rider. Because each component (B, D, R, M) is logged individually before being summed, the fare is decomposable and auditable rather than a single opaque number. This directly addresses the pricing-opacity problem identified by Acheampong (2021) as a major source of driver–passenger conflict in African ride-hailing contexts, positioning transparency as a designed outcome of the framework rather than an afterthought.

## 2.2 Theoretical Framework

This study draws on two theoretical strands. The first is the economic theory of dynamic and surge pricing in two-sided marketplaces, where a platform sets prices to balance the interests of riders, who want low fares and short waits, against those of drivers, who want to be adequately compensated for their time and, this study argues, for the risk they absorb on behalf of the platform. (Garg & Nazerzadeh, 2022) frame driver-side surge pricing explicitly around the idea that a trip imposes costs on a driver that extend beyond the immediate fare, since accepting one trip forecloses the earnings a driver might have made elsewhere in that period. The same logic extends naturally to risk: a driver who accepts a trip into a historically dangerous corridor is bearing a cost, whether in the form of vehicle damage, personal safety exposure, or simply the psychological toll of driving somewhere they would rather avoid, and a pricing model that ignores this cost is, in effect, asking the driver to absorb it for free.

The second theoretical strand comes from transportation risk and network modelling, where the cost, or disutility, of travelling along a given path is treated as a function of more than just distance and time. (Musolino, 2024) frames this in terms of a learning process, in which transport users continually update their perception of a path's cost based on both historical experience and, increasingly, real-time information delivered through internet-of-thing sensors and related technologies. The distance-risk-aware pricing model developed in this project borrows this idea directly: the risk score assigned to a route is not a fixed number decided once and never revisited, but a value that should, in a full deployment, be periodically recalculated as new incident data becomes available.

## 2.3 Empirical Framework 

A growing body of empirical work has examined dynamic pricing in ride-hailing platforms from several angles, though relatively little of it addresses route-level risk directly.

### **2.3.1 Dynamic Pricing and Equity in Ride-Hailing** 

(Cashore et al., 2022) developed a stochastic model of ride-sharing networks in which prices are recomputed continually in response to observed supply and demand, and show, using both theoretical analysis and simulation, that this kind of continual re-solving produces materially more stable outcomes than pricing schemes that are set once and left static. Their central finding, that dynamic recalculation matters more than the specific pricing rule chosen, supports the architectural decision in this project to treat the risk score as a live input recomputed per trip rather than a static lookup table.

(Schröder et al., 2020), working with price time-series collected from ride-hailing services at 137 locations worldwide, found that dynamic pricing schemes can, under certain conditions, produce anomalous and counter-productive supply shortages, where drivers collectively withhold availability to induce a price surge rather than the surge arising organically from demand. Their work is a useful caution for this project: a poorly calibrated risk surcharge could, in principle, create similar perverse incentives, for instance if drivers learned to manufacture the appearance of risk to trigger higher fares, which is one reason the risk score in this study is designed around externally verifiable historical data rather than driver-reported conditions alone.

### **2.3.2 Route Risk Prediction**

Musolino (2024) provides a framework for how transport network models can incorporate updating measures of path cost during emergency or high-risk conditions, drawing on internet-of-things and historical data sources. Separately, Yuan, Mobley, Farahmand, Xu, Blessing, Dong, Mostafavi, and Brody (2021) demonstrate that road-level risk, in their case flood risk, can be predicted with reasonable accuracy using machine learning models trained on crowdsourced reports combined with topographic and hydrologic features, which is encouraging evidence that a similar approach, adapted to whatever data is locally available, could support the risk-scoring component of a pricing system such as the one developed here, even in a data-sparse environment.

### **2.3.3 Geospatial Routing and Route Optimisation**

Randriamihaja et al. (2024) demonstrated the practical use of OpenStreetMap-derived road and footpath networks, combined with a Vehicle-Routing-Problem-with-Time-Windows optimisation algorithm and the Open Source Routing Machine (OSRM), to plan last-mile community health delivery routes in rural Madagascar. Their study is relevant to this project in two respects: it confirms that OpenStreetMap data, despite being volunteer-contributed, can support production-grade route optimisation when properly validated, and it demonstrates a reusable pattern — geographic data ingestion, routing-engine computation, and an interactive dashboard for decision-makers — that this project's Routing Service adapts for urban trip-distance computation. Stahr, Maaß, and Gärtner (2023) similarly used OpenStreetMap data to build a customised A\* routing algorithm for a mobile-robot assistance system, first validating the map data against the ISO 19157 geographic-information-quality standard before augmenting it with additional attributes and a modified cost function. Their three-stage process — validate, augment, then re-cost the routing graph — is adopted in this project's Routing Service design, where the base OpenStreetMap road graph is similarly augmented with the accident and road-condition attributes needed by the Risk Assessment Service before a route is costed and returned.

**2.4 Summary of Literature Review**

The literature reviewed in this chapter establishes three things fairly clearly. First, dynamic pricing in ride-hailing is a well-studied problem, but almost all of the existing work treats the inputs to that pricing as demand, supply, and occasionally driver-side incentives, with very little attention paid to route-level physical or safety risk as a distinct pricing input. Second, where risk is studied in the transportation literature, it tends to appear in the context of network planning, evacuation, or infrastructure resilience, rather than being connected back to how a commercial transportation service prices an individual trip. Third, the broader literature on pricing fairness and bias suggests that any new pricing input, including a risk score, must be constructed carefully to avoid reproducing existing inequities rather than addressing them. This project sits at the intersection of these three observations, proposing a pricing model that treats risk as a first-class, transparent input to fare computation, built from verifiable route and incident characteristics rather than from proxies that could disadvantage particular neighbourhoods.

**Table 1: Comparison of Dynamic Pricing Approaches**

| **Approach**                                                 | **Inputs Used**                                     | **Risk-Aware?**                                 | **Fare Transparency**                       | **Equity Safeguard**                           |
|--------------------------------------------------------------|-----------------------------------------------------|-------------------------------------------------|---------------------------------------------|------------------------------------------------|
| Flat / distance-only fare                                    | Base fare, distance                                 | No                                              | Single opaque total                         | None                                           |
| Demand-only surge pricing (Chen, 2016; Hall & Krueger, 2018) | Distance, time, request/driver ratio                | No                                              | Multiplier shown, components not decomposed | None — uncapped in most commercial deployments |
| Multi-factor taxi pricing (He et al., 2018)                  | Distance, time, penalty/compensation terms          | Partial — no route-level risk index             | Partially decomposed                        | Not addressed                                  |
| Proposed Distance-Risk-Aware Model                           | Distance (D), Route Risk (R), Demand Multiplier (M) | Yes — explicit, weighted Route Risk Coefficient | Fully decomposed and logged (B, D, R, M, F) | Configurable demand-multiplier cap (M_cap)     |

# CHAPTER THREE

**RESEARCH METHODOLOGY**

## 3.1 Methodology Adopted

We adopted an Agile, iterative software development methodology in preference to a plan-driven methodology such as the Structured Systems Analysis and Design Method (SSADM) or the classical Waterfall model. Agile development proceeds through short, repeated cycles in which a small piece of working software is built, tested, and reviewed before the next increment is started, rather than requiring the entire system to be fully specified before any code is written.

The choice of Agile over a plan-driven methodology was informed by three considerations specific to this project. First, the project integrates an external routing dependency (the OSRM API) whose response format and behaviour could only be fully understood once real calls were made against it; an iterative approach allowed the Routing module to be adjusted as this understanding developed, without requiring a complete upfront specification of every external interaction, which a Waterfall or SSADM approach would have demanded. Second, the core pricing formula required several rounds of refinement — for example, the decision to keep the additive and multiplicative fare strategies as separate, independently testable implementations (Section 4.3) emerged only after an initial version of the pricing module had already been built and tested. Third, with only two developers and a fixed academic timeline, Agile's emphasis on delivering a working increment at every stage reduced the risk of reaching the project deadline with a large amount of interdependent, untested design and no working software, which is a known weakness of heavily front-loaded methodologies such as SSADM.

The methodology was applied through the following repeated phases:

1\. **Increment Planning:** a small, testable unit of functionality was selected — for example, the risk-classification function, or a single API endpoint.

2\. **Implementation:** the unit was implemented as an independent Python module or React component, following the module boundaries described in Section 4.1.

3\. **Automated Testing:** a corresponding unit test (or set of tests) was written using Pytest, and the full test suite was run before the increment was considered complete (Section 4.8).

4\. **Integration and Review:** the new increment was integrated with the rest of the system through the API gateway, and its behaviour was manually reviewed against the mathematical specification of the fare, risk, and demand formulas.

This cycle was repeated for each module — Routing, Risk Assessment, Demand Intelligence, and the Pricing Engine — and again for the API gateway and the web client, until the full system described in Chapter Four was complete. Version control (Git) was used throughout to track each increment, and a continuous-integration workflow was configured to run the automated test suite automatically on every change, which is the specific supporting method through which the Agile cycle above was enforced in practice rather than left informal.

The principal benefit of this methodology over a plan-driven alternative was that, at every point in the project timeline, a working and tested (if incomplete) version of the system existed. This meant that the scope reductions described in Section 1.6 — for instance, using a simulated risk-data feed rather than a live one — could be made as deliberate, informed decisions partway through the project, rather than being discovered as unworkable assumptions only after a full upfront design (as could have happened under SSADM or Waterfall) had already been completed and signed off.

# CHAPTER FOUR

**SYSTEM DESIGN AND IMPLEMENTATION**

## 4.1 System Architecture

The implemented system consists of a single API gateway process that routes requests to four internal modules — a Routing module, a Risk Assessment module, a Demand Intelligence module, and a Pricing Engine — together with a PostgreSQL database that stores every computed fare quotation. Figure 4.1 shows the architecture of the system as built.

![](media/image2.png)

**Figure 4.1: System Architecture**

A web client, built with Next.js, communicates with the API gateway over HTTPS. The gateway forwards each fare request to the four internal modules in turn: The Routing module calls the public OSRM API to obtain the distance between the origin and destination; the Risk Assessment module computes a route risk coefficient; the Demand Intelligence module computes a demand multiplier; and the Pricing Engine combines the three results into a final fare, which is written to the database and returned to the client. The four modules are implemented as separate, independently testable Python packages that communicate through in-process function calls behind the single gateway, rather than as four independently deployed network services; each module's internal logic does not depend on this, so it can be extracted into its own deployable service without modification if required.

## 4.2 Tools and Technologies Used

Table 4.1 lists the technologies used to build the system.

| **Layer**            | **Technology**                        | **Role**                                                       |
|----------------------|---------------------------------------|----------------------------------------------------------------|
| Frontend             | Next.js (React, TypeScript)           | Web client exposing fare-estimate, risk, and methodology pages |
| Backend API          | FastAPI (Python)                      | REST API gateway and the four internal modules                 |
| Data validation      | Pydantic                              | Request and response schema validation for the API gateway     |
| Database             | PostgreSQL, hosted on Neon            | Persistent store for computed fare quotations                  |
| ORM / migrations     | SQLAlchemy with Alembic               | Object-relational mapping and versioned schema migrations      |
| Routing data         | OpenStreetMap via the public OSRM API | Shortest-path distance and route computation                   |
| Testing              | Pytest; Vitest (frontend)             | Automated unit and API tests                                   |
| Version control / CI | Git; GitHub Actions                   | Source control and automated test execution on every commit    |

**Table 4.1: Technology Stack**

## 4.3 Database Design

The implemented system persists one table, fare_quotes, with one row written per completed fare quotation. Each row stores the request coordinates, the computed distance and duration, the risk score and its classification, the demand multiplier, the full component breakdown of the fare (base, distance, risk, and demand adjustments and the total), the formula variant used, and a summary of where the risk and demand values were sourced from. This design was chosen so that every fare returned by the system is independently auditable from the database alone, without needing to re-run the computation. Table 4.2 lists the principal fields of the schema.

| **Field**                                                                     | **Type**         | **Description**                                                                                   |
|-------------------------------------------------------------------------------|------------------|---------------------------------------------------------------------------------------------------|
| id                                                                            | String (UUID)    | Primary key uniquely identifying the quotation                                                    |
| requested_at / created_at                                                     | Timestamp        | When the fare was requested and when the record was written                                       |
| origin_latitude / origin_longitude                                            | Numeric          | Coordinates of the trip origin                                                                    |
| destination_latitude / destination_longitude                                  | Numeric          | Coordinates of the trip destination                                                               |
| distance_km                                                                   | Numeric          | Trip distance (D) computed by the Routing module                                                  |
| estimated_duration_minutes                                                    | Integer          | Estimated trip duration returned by OSRM                                                          |
| risk_score / risk_classification                                              | Numeric / String | Route Risk Coefficient (R) and its Low/Moderate/High/Very High classification                     |
| demand_multiplier                                                             | Numeric          | Demand Multiplier (M) applied to the fare                                                         |
| base_fare, distance_component, risk_adjustment, demand_adjustment, total_fare | Numeric          | The individually logged components of the Fare Function and their sum                             |
| formula_mode / formula_version / pricing_coefficient_version                  | String           | Which fare formula (additive or multiplicative) and coefficient set produced this quotation       |
| risk_source_summary / demand_source_type                                      | Text / String    | Record of whether the R and M values were observed, questionnaire-derived, external, or simulated |

**Table 4.2: Fare Quotation Database Schema**

## 4.4 Pricing, Risk, and Demand Model Implementation

The Pricing Engine computes the final fare using the Fare Function:

F = B + (α × D) + (β × D × R) + (γ × M) ….. (1)

where F is the computed fare, B is the base fare, D is the distance in kilometres returned by the Routing module, R is the Route Risk Coefficient, M is the Demand Multiplier, and α, β, and γ are configurable coefficients. The base fare, distance component, risk component, and demand component are computed and stored as four separate values before being summed, so that the breakdown persisted in Table 4.2 is exact rather than reconstructed after the fact. A second, multiplicative formula, F = \[B + αD + βDR\] × M, is also implemented as a selectable alternative strategy; the additive form in Equation (1) is the default used throughout this study because it keeps the demand contribution linearly interpretable and independent of the risk premium.

The Risk Assessment module computes the Route Risk Coefficient as:

R = w₁ × R_acc + w₂ × R_road + w₃ × R_sec (2)

where R_acc, R_road, and R_sec are the normalised accident, road-quality, and security sub-indices, and w₁, w₂, w₃ are non-negative weights that the module requires to sum to 1.0, raising a configuration error otherwise. Each sub-index value is tagged with a source type of observed, questionnaire, derived, external, or simulated; in the current implementation, the sub-index values are produced by simulated and questionnaire-derived data, consistent with the limitation recorded in Section 1.6, and this tag travels with the value into the fare_quotes record described in Table 4.2 so that a simulated figure is never presented as a verified observation. The resulting score is classified into one of four bands, shown in Table 4.3.

| **Classification** | **R Score Range** | **System Behaviour**                                     |
|--------------------|-------------------|----------------------------------------------------------|
| Low                | 0.00 – 0.25       | Base distance rate only; no risk premium applied         |
| Moderate           | 0.26 – 0.50       | A moderate risk premium is applied through the βDR term  |
| High               | 0.51 – 0.75       | A higher risk premium is applied through the βDR term    |
| Very High          | 0.76 – 1.00       | The maximum risk premium is applied through the βDR term |

**Table 4.3: Risk Classification Bands**

The Demand Intelligence module computes the Demand Multiplier as:

M = min(1 + λ × (Req / Sup − 1), M_cap) (3)

where Req and Sup are the number of active ride requests and available drivers in the origin zone, λ is a configurable sensitivity parameter, and M_cap is a configurable upper bound (set to 2.5 by default in the reference configuration). When Req/Sup is at or below 1.0, the module returns M = 1.0, so a fare is never discounted below its base distance cost. As with the Risk module, Req and Sup are currently produced by a simulated ride-request and driver-availability feed and are tagged with a source type of observed, external, or simulated, consistent with the limitation recorded in Section 1.6.

## 4.5 Use Case Design

Figure 4.2 presents the use case diagram for the implemented system. A single external actor, the Passenger, interacts with the system to request a fare estimate or retrieve a previously computed quotation. Requesting a fare estimate includes four internal use cases — computing the route distance, the risk coefficient, the demand multiplier, and the final fare — the first of which is the only interaction that calls an external system, the OSRM Routing API.

![](media/image3.png)

**Figure 4.2: Use Case Diagram for the Pricing System**

## 4.6 API Design

The API gateway exposes a versioned REST interface under the base path /api/v1, implemented with FastAPI and documented automatically as an OpenAPI schema. Table 4.4 lists the endpoints implemented in the system.

**Table 4.4: Implemented REST API Endpoints**

| **Method** | **Path**                 | **Purpose**                                                     |
|------------|--------------------------|-----------------------------------------------------------------|
| GET        | /health                  | Liveness check                                                  |
| GET        | /ready                   | Dependency readiness check                                      |
| GET        | /metrics                 | Request counters and durations, in Prometheus-compatible format |
| POST       | /api/v1/routes/estimate  | Compute route distance D between an origin and destination      |
| POST       | /api/v1/risk/estimate    | Compute the Route Risk Coefficient R for a route                |
| POST       | /api/v1/fares/estimate   | Compute and persist a full fare quotation (D, R, M, F)          |
| GET        | /api/v1/fares/{quote_id} | Retrieve a previously computed fare quotation                   |

*Source: Author's implementation, 2026*

A client requests a fare by submitting an origin and destination coordinate pair to /api/v1/fares/estimate. The gateway calls the Routing module to obtain the distance, passes the route to the Risk module to obtain R, queries the Demand module for the origin zone's M, applies Equation (1), and returns a response containing the route distance and duration, the risk score and classification, the demand multiplier, and the full fare breakdown. The same response body is written to the fare_quotes table described in Section 4.3.

## 4.7 User Interface Design

A Next.js web client was implemented to exercise the API described in Section 4.6. Table 4.5 lists the pages implemented in the system.

**Table 4.5: Implemented Frontend Pages**

| **Route**    | **Purpose**                                                                            |
|--------------|----------------------------------------------------------------------------------------|
| /            | Landing page introducing the pricing system                                            |
| /estimate    | Form for submitting an origin/destination pair and viewing the returned fare breakdown |
| /risk        | Explanation of the Route Risk Coefficient and the classification bands of Table 4.3    |
| /methodology | Summary of the pricing methodology, linked back to Chapter Two                         |
| /about       | Project and author information                                                         |

*Source: Author's implementation, 2026*

## 4.8 Benefits of the Implemented System

| **\#** | **Benefit**             | **Description**                                                                                                                                                                                                                                                  |
|--------|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1      | Driver Fairness         | Trips through higher-risk routes attract a proportionally higher risk premium through the βDR term, addressing the systemic under-compensation documented by Acheampong (2021) for drivers on challenging urban corridors.                                       |
| 2      | Passenger Transparency  | Every fare is logged as a decomposable breakdown (B, D, R, M, F) in the database, addressing the pricing-opacity concern identified in the literature.                                                                                                           |
| 3      | Bounded Demand Response | The capped Demand Multiplier (M_cap) prevents unconstrained fare surges, directly implementing the equity safeguard called for by Lokhandwala and Cai (2018).                                                                                                    |
| 4      | Source Honesty          | Every risk and demand value is tagged with its source type (observed, questionnaire, derived, external, or simulated), so a simulated figure is never presented as a verified observation.                                                                       |
| 5      | Modularity              | The Routing, Risk, Demand, and Pricing modules are independently implemented and independently tested (Section 4.9), so any one of them can be replaced — for example, by connecting the Risk module to a live accident-data feed — without changing the others. |
|        |                         |                                                                                                                                                                                                                                                                  |

**Table 4.6: Benefits of the Implemented Pricing Model**

## 4.9 Testing

The system was verified using an automated Pytest suite covering the backend modules, together with a component test for the frontend fare-breakdown display, written with Vitest. A GitHub Actions workflow runs the full suite on every commit. Table 4.7 summarises the test coverage by module.

| **Module**                        | **Test File**              | **Number of Tests** |
|-----------------------------------|----------------------------|---------------------|
| API Gateway                       | test_api.py                | 8                   |
| Demand Intelligence               | test_demand.py             | 5                   |
| Pricing Engine                    | test_pricing.py            | 4                   |
| Risk Assessment                   | test_risk.py               | 3                   |
| Routing                           | test_routing.py            | 3                   |
| Service boundary contracts        | test_service_boundaries.py | 3                   |
| External provider adapters        | test_external_providers.py | 2                   |
| Frontend fare-breakdown component | fare-breakdown.test.tsx    | 1                   |

**Table 4.7: Unit Test Coverage by Module**

The test suite verifies, among other things, that the Pricing Engine correctly sums the four fare components for both the additive and multiplicative strategies, that the Risk module correctly classifies scores into the four bands of Table 4.3 and rejects risk weights that do not sum to 1.0, that the Demand module correctly bounds the multiplier at M_cap and returns 1.0 when supply meets or exceeds demand, and that the API gateway returns the expected response shape for a complete fare request. All 29 automated tests pass on the current version of the system.

## 4.10 System Documentation Summary

This chapter has documented the system as implemented: a single API gateway coordinating four internal modules (Section 4.1), built with the technologies listed in Table 4.1, persisting one fare_quotes table per completed request (Section 4.3), computing the fare using Equations (1)–(3) exactly as coded (Section 4.4), exposed through the endpoints of Table 4.4 (Section 4.6), and presented through the web pages of Table 4.5 (Section 4.7). Every part of this chapter describes software that exists in the project repository and is exercised by the automated test suite summarised in Table 4.7; Chapter Five discusses what these results mean and what would be required to extend the system beyond its current scope.

**  
**

# LIST OF REFERENCES

Acheampong, R. A. (2021): “Societal impacts of smart, digital platform mobility services — an empirical study and policy implications of passenger safety and security in ride-hailing”, in: Case Studies on Transport Policy, Vol. 9, No. 1, pp. 302-314. Available at: https://doi.org/10.1016/j.cstp.2021.01.008

Bast, H., Delling, D., Goldberg, A., Müller-Hannemann, M., Pajor, T., Sanders, P., Wagner, D., & Werneck, R. F. (2016): “Route Planning in Transportation Networks”, in Kliemann, L. & Sanders, P. (eds.), Algorithm Engineering: Selected Results and Surveys, Lecture Notes in Computer Science Vol. 9220, Springer, Cham, pp. 19-80. Available at: https://doi.org/10.1007/978-3-319-49487-6_2

Bayer, M. (2006): SQLAlchemy — The Python SQL Toolkit and Object Relational Mapper. Available at: https://www.sqlalchemy.org

Brodsky, I. (2018): H3: Uber's Hexagonal Hierarchical Spatial Index, Uber Engineering Blog. Available at: https://www.uber.com/en-NG/blog/h3/

Cachon, G. P., Daniels, K. M., & Lobel, R. (2017): “The Role of Surge Pricing on a Service Platform with Self-Scheduling Capacity”, in: Manufacturing & Service Operations Management, Vol. 19, No. 3, pp. 368-384. Available at: https://doi.org/10.1287/msom.2017.0618

Chen, M. K. (2015): “Dynamic Pricing in a Labor Market: Surge Pricing and Flexible Work on the Uber Platform”, in: Proceedings of the 2016 ACM Conference on Economics and Computation (EC'16), Maastricht, the Netherlands, p. 455. Available at: https://doi.org/10.1145/2940716.2940798

Colvin, S. (2017): Pydantic — Data Validation Using Python Type Hints. Available at: https://docs.pydantic.dev

Hall, J. V., & Krueger, A. B. (2018): “An Analysis of the Labor Market for Uber's Driver-Partners in the United States”, in: ILR Review, Vol. 71, No. 3, pp. 705-732. Available at: https://doi.org/10.1177/0019793917717222

He, F., Wang, X., Lin, X., & Tang, X. (2018): “Pricing and penalty/compensation strategies of a taxi-hailing platform”, in: Transportation Research Part C: Emerging Technologies, Vol. 86, pp. 263-279. Available at: https://doi.org/10.1016/j.trc.2017.11.003

Krekel, H., Oliveira, B., Pfannschmidt, R., et al. (2004): pytest — Full-Featured Python Testing Tool. Available at: https://pytest.org

Lee, J., Nam, B., & Abdel-Aty, M. (2015): “Effects of Pavement Surface Conditions on Traffic Crash Severity”, in: Journal of Transportation Engineering, Vol. 141, No. 10, pp. 04015020. Available at: https://doi.org/10.1061/(ASCE)TE.1943-5436.0000785

Lokhandwala, M., & Cai, H. (2018): “Dynamic ride sharing using traditional taxis and shared autonomous taxis: A case study of NYC”, in: Transportation Research Part C: Emerging Technologies, Vol. 97, pp. 45-60. Available at: https://doi.org/10.1016/j.trc.2018.10.007

Neon, Inc. (2022): Neon — Serverless Postgres. Available at: https://neon.tech

PostgreSQL Global Development Group (1996): PostgreSQL: The World's Most Advanced Open Source Relational Database. Available at: https://www.postgresql.org

Ramírez, S. (2018): FastAPI — Modern, High-Performance Web Framework for Building APIs with Python. Available at: https://fastapi.tiangolo.com

Vercel Inc. (2016): Next.js — The React Framework for the Web. Available at: https://nextjs.org

Yao, H., Wu, F., Ke, J., Tang, X., Jia, Y., Lu, S., Gong, P., Ye, J., & Li, Z. (2018): “Deep Multi-View Spatial-Temporal Network for Taxi Demand Prediction”, in: Proceedings of the Thirty-Second AAAI Conference on Artificial Intelligence (AAAI-18), New Orleans, Louisiana, pp. 2588-2595. Available at: https://doi.org/10.1609/aaai.v32i1.11836
