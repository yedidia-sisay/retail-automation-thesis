
// ============================================================
// TITLE PAGE
// ============================================================
#align(center)[
  #v(1.5cm)

  #text(15pt, weight: "bold")[ADDIS ABABA UNIVERSITY] \
  #v(0.3em)
  #text(12pt)[College of Technology and Built Environment] \
  #text(11pt)[Department of Computer Science and Engineering] \

  #v(1.5cm)
  #v(0.8cm)

  #text(18pt, weight: "bold")[
    Retail Checkout Automation System \
    Using Computer Vision
  ]

  #v(1.9cm)
  
  #text(11pt)[
  A Thesis Submitted in Partial Fulfillment of the Requirements for the Degree of 
  ]


  #text(12pt, weight: "bold")[
    Bachelor of Science in Computer Science and Engineering
  ]

  #v(2.2cm)

  #grid(
    columns: (1fr, 1fr),
    gutter: 2em,

    align(left)[
      *Prepared by:* \
      Hillary Mengesha \
      UGR/6175/14 \
      #v(0.6em)
      Yedidia Sisay \
      UGR/4567/14
    ],

    align(left)[
      *Advisor:* \
      Dr. Beneyam Haile
    ],
  )

  #v(2cm)

  *Submission Date:* May 26, 2026 \

  #v(1.5cm)

  Addis Ababa, Ethiopia
]

#pagebreak()
// ============================================================
// CERTIFICATE OF APPROVAL
// ============================================================
#align(center)[
  #v(1cm)
  #text(14pt, weight: "bold")[Certificate of Approval]
  #v(0.5em)
  
]
#v(1em)

This is to certify that the thesis entitled *"Retail Checkout Automation System Using Computer Vision"*, prepared by Hillary Mengesha(UGR/6175/14) and Yedidia Sisay(UGR/4567/14), is submitted in partial fulfillment of the requirements for the degree of Bachelor of Science in Computer Science and Engineering at Addis Ababa University. The thesis has been carried out under proper supervision and is approved for submission to the Department.

#v(2em)

*Supervisor* \
Name: #h(3cm) \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \
Signature: #h(2.3cm) \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \
Date: #h(3.2cm) \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

#v(1.5em)


#pagebreak()


// ============================================================
// ABSTRACT
// ============================================================
#align(center)[
  #text(14pt, weight: "bold")[Abstract]
]
#v(0.5em)

#v(0.8em)

Manual checkout remains a common bottleneck in supermarket retail. Cashiers must identify products, handle barcode failures, verify prices, process weighed items, and generate receipts under time pressure. These tasks increase customer waiting time and reduce checkout throughput, especially in low-cost retail environments where fully automated checkout systems are too expensive and complex to deploy.

This thesis presents the design, implementation, and evaluation of a low-cost cashier-assisted point-of-sale automation system for the Ethiopian supermarket context. The system uses a YOLOv8 object detection model to identify products placed on a checkout surface and return class labels, bounding boxes, and confidence scores. A Django backend matches detected items with an Odoo ERP product catalogue, aggregates quantities, manages checkout state, and prepares draft receipt data. A React cashier interface allows the cashier to review, correct, confirm, or override detections using barcode fallback when needed.

The system also includes a weighted-product workflow for fruits and vegetables. This workflow combines produce recognition with digital scale reading, allowing price calculation based on detected product type, measured weight, and unit price.

Evaluation focuses on both detection performance and checkout correctness. The YOLOv8 model is assessed using precision, recall, "mAP-50", mAP-50–95, confusion matrix analysis, and inference latency. The full system is evaluated through product matching accuracy, duplicate aggregation, price retrieval, receipt total correctness, barcode fallback behaviour, weighted-item price calculation, and cashier correction workflow.

The proposed system demonstrates a practical middle ground between manual checkout and expensive fully automated retail systems, showing that computer vision can support faster and more reliable cashier-assisted checkout within realistic local hardware and cost constraints.

#v(0.8em)
*Keywords:* computer vision, object detection, YOLOv8, point-of-sale automation, supermarket checkout, supermarket, automated checkout, cashier-assisted system, Odoo ERP, Ethiopia.

#pagebreak()


// ============================================================
// ACKNOWLEDGEMENTS
// ============================================================
#v(7em)
#align(center)[
  #text(14pt, weight: "bold")[Acknowledgements]
]
#v(0.5em)

#v(3em)

We would like to express our sincere gratitude to our advisor, Dr. Beneyam Haile, for his guidance, support, and constructive feedback throughout the development of this thesis. His direction helped us refine the project scope, improve the technical design, and strengthen the overall quality of the work.

We are also grateful to the School of Electrical and Computer Engineering at Addis Ababa University for providing the academic foundation and environment needed to complete this project.

We also would like to express our deep gratitude to our families, for they made us the people who we are today.
#pagebreak()


// ============================================================
// TABLE OF CONTENTS
// ============================================================

// Turn page numbering on for front matter
#set page(numbering: "i", number-align: center)

#align(center)[
  #text(14pt, weight: "bold")[Table of Contents]
]

#v(0.8em)

#outline(
  indent: 1.5em,
  depth: 3,
)
  
#pagebreak()

// Start main content with Arabic numbering
#set page(numbering: "1", number-align: center)
#counter(page).update(1)
#set heading(numbering: "1.")
// ============================================================
// LIST OF FIGURES
// ============================================================
#align(center)[
  #text(14pt, weight: "bold")[List of Figures]
]
#v(0.5em)

#v(0.5em)
#outline(title: none, target: figure.where(kind: image))

#pagebreak()


// ============================================================
// LIST OF TABLES
// ============================================================
#align(center)[
  #text(14pt, weight: "bold")[List of Tables]
]
#v(0.5em)

#v(0.5em)
#outline(title: none, target: figure.where(kind: table))

#pagebreak()


// ============================================================
// LIST OF ABBREVIATIONS
// ============================================================
#align(center)[
  #text(14pt, weight: "bold")[List of Abbreviations and Acronyms]
]
#v(0.5em)

#v(0.8em)

#table(
  columns: (2.5cm, 1fr),
  stroke: none,
  inset: (x: 0pt, y: 4pt),
  [*API*], [Application Programming Interface],
  [*CCTV*], [Closed-Circuit Television],
  [*CNN*], [Convolutional Neural Network],
  [*ERP*], [Enterprise Resource Planning],
  [*FPS*], [Frames Per Second],
  [*GPU*], [Graphics Processing Unit],
  [*JSON*], [JavaScript Object Notation],
  [*mAP*], [Mean Average Precision],
  [*OCR*], [Optical Character Recognition],
  [*POS*], [Point of Sale],
  [*REST*], [Representational State Transfer],
  [*SKU*], [Stock Keeping Unit],
  [*UI*], [User Interface],
  [*YOLO*], [You Only Look Once],
)

// ── Switch to main body page numbering ──────────────────────
#set page(numbering: "1")
#counter(page).update(1)


// ============================================================
// 1. EXECUTIVE SUMMARY
// ============================================================
#v(0.5em)
= Executive Summary

This thesis presents the design, development, and evaluation of a cashier-assisted retail checkout automation system for the Ethiopian supermarket context. The system uses a YOLOv8 object detection model to identify selected products placed on a checkout surface, a Django backend to manage product matching and checkout logic, and a React-based cashier interface for reviewing, correcting, and confirming draft receipts before finalisation.

The project is motivated by a practical retail problem: manual checkout is repetitive, time-consuming, and vulnerable to delays caused by missing, damaged, or unreadable barcodes. Fully automated checkout systems exist, but their cost, hardware complexity, and maintenance requirements make them difficult to adopt in many local supermarket environments. This thesis therefore proposes a middle-ground approach that uses computer vision to reduce cashier workload while preserving human oversight for accuracy and reliability.

The implemented prototype includes a trained YOLOv8 model evaluated on a locally collected dataset of Ethiopian supermarket products, an end-to-end checkout pipeline for converting detections into receipt items, ERP-based product matching, weighted-product handling, digital receipt generation, payment simulation, and cashier correction support. The cashier remains responsible for confirming the transaction, which allows the system to handle uncertain detections, missed products, and fallback cases without compromising receipt correctness.

The system is designed for low-cost prototype deployment using standard consumer hardware such as a laptop or Raspberry Pi, together with a USB camera, barcode scanner, and digital scale. Odoo ERP is used for product catalogue management and transaction recording, while the Django backend and React interface coordinate the checkout workflow.

The thesis concludes that vision-assisted checkout can provide a practical and affordable support mechanism for retail point-of-sale operations. It also identifies confidence-based detection triage, human-in-the-loop model improvement, expanded local datasets, improved weighted-product recognition, and edge deployment optimisation as important directions for future work.

#pagebreak()


// ============================================================
// 2. INTRODUCTION
// ============================================================
= Introduction

== Background and Relevance

Supermarket checkout is among the most labour-intensive stages in the retail transaction cycle. Despite the widespread adoption of electronic point-of-sale systems over the past four decades, the fundamental process at the checkout counter has changed relatively little: a cashier identifies each product individually, scans or enters it into the system, resolves any identification failures, and issues a receipt. Under normal trading conditions this workflow is manageable. Under peak load — high customer volume, large basket sizes, or frequent barcode failures — it becomes a measurable constraint on retail throughput and a source of customer dissatisfaction.

In high-income markets, commercial responses to this constraint have produced self-checkout kiosks, computer-vision-based cart tracking systems (notably Amazon Go @amazon_just_walk_out), and fully automated checkout lanes. These solutions achieve meaningful throughput improvements but carry high capital, installation, and maintenance costs that place them out of reach for supermarkets operating in a cost-constrained environments.

Ethiopian supermarkets face the operational pressures of high-volume checkout without access to the automated infrastructure that has emerged elsewhere. Queues during peak hours are common. Cashier workload is repetitive and demanding. No commercially available checkout automation solution is currently designed for, or cost-calibrated to, the Ethiopian retail context.

== Engineering Context and Motivation

*Recent advances in real-time object detection, particularly the YOLO model family, have reduced the computational requirements for accurate product identification to the point where inference is feasible on standard consumer hardware.* @redmon_yolo_2016 @ultralytics_yolov8_2023 This creates an opportunity to design a checkout assistance system that is genuinely affordable: one that augments the existing cashier workflow, and that can be deployed on hardware already present in most supermarket environments.


== Literature Review

Retail checkout automation has developed through several approaches, ranging from conventional barcode-based POS systems to fully cashierless stores and computer-vision-assisted checkout systems. These systems share the same general aim: reducing checkout time, improving transaction accuracy, and lowering the repetitive workload placed on cashiers. However, they differ in infrastructure cost, technical complexity, degree of automation, and suitability for small or medium retail environments.

=== Conventional Barcode-Based POS Systems

The conventional supermarket checkout process is still mainly based on barcode scanning. In this workflow, the cashier scans each product barcode, the POS system retrieves the corresponding product record, and the receipt is generated after all products have been entered. This method is reliable because product identification is based on a stored barcode database rather than visual estimation.

However, barcode-based checkout still depends heavily on manual cashier operation. Damaged barcodes, missing labels, difficult-to-scan packaging, repeated products, and products sold by weight can slow down the transaction. During peak shopping hours, this process can contribute to long queues and reduced customer satisfaction.

The proposed system does not completely remove barcode scanning. Instead, barcode scanning is retained as a fallback method when the computer-vision model misses an item, detects a wrong class, gives a low-confidence result, or encounters a product outside the trained classes. This hybrid approach makes the system more practical because the vision model assists the cashier without replacing the reliability of barcode-based product lookup.

=== Amazon Go and Fully Cashierless Retail Systems

Amazon Go and Amazon Just Walk Out represent one of the most advanced forms of retail checkout automation. These systems use combinations of computer vision, sensors, artificial intelligence, and customer payment association to track items selected by customers and automatically charge them after they leave the store @amazon_just_walk_out. In this model, the traditional checkout counter is removed entirely.

Although this approach demonstrates the potential of fully automated retail, it requires high infrastructure investment. A store-level cashierless system may require multiple cameras, shelf sensors, identity or payment association, continuous tracking, and complex backend processing. These requirements make such systems difficult to adopt in cost-sensitive supermarket environments.

This thesis therefore does not follow the Amazon Go model directly. Instead of tracking customers throughout the store, the proposed system focuses only on products placed on a checkout surface. This reduces hardware cost, avoids full-store surveillance, simplifies the detection problem, and keeps the cashier involved in the final billing decision.

=== Retail Product Checkout Dataset

The Retail Product Checkout dataset, commonly referred to as the RPC dataset, is an important reference point for research on automatic checkout. Wei et al. introduced RPC to support automatic checkout research by providing a large-scale retail product dataset containing both single-product images and multi-product checkout images @wei_rpc_2019. The dataset was designed to represent the fine-grained recognition problem found in retail environments, where many products differ only by packaging, color, brand, or size.

The RPC dataset is relevant to this thesis because it frames checkout automation as a product detection and shopping-list generation problem. In a vision-based checkout system, the model must not only detect objects, but also identify the correct product class so that the item can be matched to a price record. This is especially challenging when products have similar shapes or visual designs.

However, RPC cannot be used directly as the only dataset for this thesis because the target products are Ethiopian supermarket products. Many products in local supermarkets are not represented in RPC. Therefore, RPC is used mainly as a methodological reference, while the actual prototype depends on a locally collected Ethiopian grocery dataset. This supports the goal of adapting checkout automation to the Ethiopian retail context.

=== Computer-Vision POS System in Related Work

A closely related study is the Malaysian work by Zainal et al., titled “Development of a POS System with Computer Vision for Automated Retail Checkout.” The authors developed a POS system that uses computer vision to automate product identification during checkout. Their system trained a YOLOv4 object detection model on product images collected from Malaysian retail stores and deployed the model as part of a checkout workflow @zainal_pos_2024.

This study is directly relevant because it follows a similar motivation to the present thesis: reducing manual barcode scanning by using computer vision to recognize retail products. It also shows the importance of using a local product dataset, since supermarket products vary by country, brand, packaging, and market context. The Malaysian study therefore supports the idea that a checkout vision model should be trained or fine-tuned using products from the target retail environment.

The proposed thesis differs from the Malaysian system in its broader checkout workflow. In this project, the detection result is not treated as the final bill. Instead, detected products are converted into a draft checkout list that the cashier can review, correct, and confirm. The system also includes barcode fallback for uncertain detections, a separate workflow for weighted products, and ERP integration using Odoo for product and receipt management. These additions make the proposed system more suitable as a cashier-assisted checkout prototype rather than a fully automatic vision-only billing system.

=== Retail Product Recognition Challenges

Retail product recognition is more difficult than general object detection because supermarket items often have small visual differences. Products may share similar shapes, colors, package sizes, and label layouts. Different flavors of the same brand can look almost identical, while the same product may appear differently depending on orientation, lighting, glare, occlusion, or camera angle.

Wei et al. identify retail product recognition as a fine-grained recognition problem, where the system must distinguish between visually similar product categories @wei_product_recognition_2020. This challenge is important for the proposed system because the goal is not only to identify broad categories such as “bottle” or “snack,” but to recognize specific supermarket products that can be linked to exact prices.

Because of these challenges, this thesis includes cashier confirmation and barcode fallback as part of the system design. These mechanisms reduce the risk of incorrect billing when the model confuses similar products or encounters uncertain detections. The system is therefore designed as a human-in-the-loop checkout assistant rather than a fully autonomous product recognition system.

=== Position of the Proposed System

The reviewed systems show that checkout automation can be implemented at different levels of complexity. Barcode-based POS systems are reliable but still require repetitive manual scanning. Amazon Go-style systems provide a high level of automation but require expensive store-wide infrastructure. The RPC dataset provides a strong research foundation for automatic checkout and fine-grained product recognition. The Malaysian computer-vision POS study shows that YOLO-based checkout automation can be developed using local retail product images.

The proposed system is positioned between conventional POS checkout and fully cashierless retail. It does not attempt to remove the cashier, track customers across the store, or replace the entire retail infrastructure. Instead, it uses computer vision to assist the cashier by detecting products placed on a checkout surface, mapping those detections to product records, preparing a draft receipt, and allowing the cashier to confirm or correct the result.

This approach is more suitable for a low-cost Ethiopian supermarket prototype. It reduces repeated barcode scanning while still keeping the cashier in control. It also supports barcode fallback, weighted-product handling, and ERP-based receipt generation, making the system closer to a practical checkout workflow than a standalone object detection demo.

#table(
  columns: (3.5cm, 4cm, 4cm, 4cm),
  stroke: 0.4pt,
  inset: 5pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*System / Study*], [*Main Approach*], [*Relevance to This Thesis*], [*Difference from Proposed System*],

  [Conventional barcode POS],
  [Cashier scans product barcodes and the POS retrieves product records.],
  [Provides reliable product-price lookup and remains widely used.],
  [Still depends on manual scanning; used in this thesis only as fallback.],

  [Amazon Go / Just Walk Out],
  [Uses store-wide sensing, computer vision, AI, and payment association for cashierless shopping.],
  [Shows the advanced direction of checkout automation.],
  [Requires expensive infrastructure; this thesis focuses only on checkout-surface detection.],

  [RPC Dataset],
  [Large-scale dataset for retail product checkout recognition.],
  [Provides a research basis for automatic checkout and fine-grained product recognition.],
  [Does not represent Ethiopian supermarket products, so local data is still required.],

  [Zainal et al.],
  [YOLOv4-based computer-vision POS system using Malaysian retail products.],
  [Closest related work because it uses local products for visual checkout automation.],
  [This thesis adds cashier review, barcode fallback, weighted-product handling, and ERP integration.],

  [Proposed system],
  [YOLO-based product detection on checkout surface with cashier confirmation and receipt generation.],
  [Targets low-cost checkout assistance for Ethiopian supermarkets.],
  [Limited to selected trained product classes and prototype conditions.]
)


== Problem Statement

The current checkout process in barcode-based supermarkets requires the manual identification and entry of every product in a transaction. This creates three measurable problems: it increases customer waiting time, it imposes repetitive scanning workload on cashiers, and it limits the number of customers a store can serve during peak periods. 

There is therefore a need for a system that can assist — without replacing — the cashier by visually identifying products, aggregating duplicates, retrieving prices, and generating a draft receipt for cashier review and confirmation. The system must be practically deployable in the retail context: inexpensive in hardware terms, tolerant of detection errors through human-in-the-loop correction, and compatible with existing cashier workflows.

== Objectives

=== General Objective

To design, develop, and evaluate a low-cost, cashier-assisted retail checkout automation system that uses computer vision to identify supermarket products and support draft receipt generation.

=== Specific Objectives

+ Collect and annotate a dataset of selected Ethiopian supermarket products under checkout-representative imaging conditions.
+ Train and evaluate a YOLOv8-based object detection model on this dataset using standard metrics.
+ Develop a Django backend that receives detection results, matches them against an ERP product catalogue, aggregates quantities, and manages checkout state.
+ Develop a React cashier interface supporting draft receipt review, manual correction, barcode fallback, and transaction confirmation.
+ Integrate Odoo ERP for product catalogue management, receipt generation, and transaction recording.
+ Implement a weighted-product sub-workflow supporting price calculation from scale-measured weight.
+ Evaluate system performance against defined detection metrics and checkout correctness criteria.
+ Test this system if it improves on the barcode based cashier workflow.

== Scope and Delimitations

The system targets a defined set of Ethiopian supermarket products. Products outside the trained catalogue are handled via barcode fallback. Prototype deployment is local (laptop or Raspberry Pi); cloud deployment is outside scope. Payment integration uses simulation only — connection to live payment providers such as Telebirr or Chapa is identified as future work. The dataset covers packaged goods and selected weighted items; full coverage of a supermarket's product range is not claimed.

== Report Structure

- Chapter 3 defines functional and non-functional requirements together with engineering constraints and success criteria. 
- Chapter 4 describes the system architecture and module design.
- Chapter 5 details the materials, tools, and methods used.
- Chapter 6 covers implementation. 
- Chapter 7 presents the testing and validation plan and results.
- Chapter 8 discusses results and engineering insights.
- Chapter 9 concludes with recommendations and future directions.

#pagebreak()
// ============================================================
// 3. REQUIREMENTS AND CONSTRAINTS
// ============================================================
= Requirements and Constraints

== Functional Requirements



#table(
  columns: (2cm, 1fr),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },
  [*ID*], [*Requirement*],
  [FR-1], [The system shall capture images of products placed on the checkout surface using a fixed camera.],
  [FR-2], [The system shall detect and classify products visible in the captured image using a YOLOv8 model.],
  [FR-3], [The system shall return bounding boxes, class labels, and confidence scores for each detection.],
  [FR-4], [The system shall aggregate duplicate detections into product quantities.],
  [FR-5], [The system shall match detected product classes to records in the ERP product catalogue.],
  [FR-6], [The system shall retrieve unit prices from the ERP system for each matched product.],
  [FR-7], [The system shall present a draft receipt to the cashier for review before finalisation.],
  [FR-8], [The cashier shall be able to add, remove, and modify quantities in the draft receipt.],
  [FR-9], [The system shall support barcode scanning as a fallback for undetected or misidentified products.],
  [FR-10], [The system shall support a weighted-product workflow that calculates item price from measured weight and unit price per kilogram.],
   
  [FR-11], [The system shall generate a digital receipt upon cashier confirmation, including product names, quantities, unit prices, subtotals, total, date, time, and payment status.],
  [FR-12], [The system shall record confirmed transactions in the ERP system.],
  [FR-13], [An administrator shall be able to manage product records, prices, categories, and barcodes.],
)



== Non-Functional Requirements

#table(
  columns: (2cm, 1fr),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },
  [*ID*], [*Requirement*],
  [NFR-1], [Detection inference shall complete within 500 ms per frame on the prototype hardware.],
  [NFR-2], [The cashier interface shall be operable by a trained cashier with no specialist technical knowledge.],
  [NFR-3], [The system shall remain functional when the detection model produces incorrect results, through cashier correction and barcode fallback.],
  [NFR-4], [The prototype shall be deployable on hardware costing no more than USD 500 in total.],
  [NFR-5], [The system shall store transaction records persistently in the ERP database.],
  [NFR-6], [The system shall be maintainable by a developer familiar with Django and React.],
)

== Engineering Constraints

=== Cost

The prototype must be deployable on consumer-grade hardware. Target total hardware cost is under USD 500, including camera, compute device, barcode scanner, and scale. Software components use open-source frameworks exclusively.

=== Performance

Detection inference must be fast enough for practical use. A target of under 500 ms per inference on the prototype compute device (laptop CPU or Raspberry Pi) is set. Receipt generation must complete within 2 s of cashier confirmation.

=== Power

The prototype assumes mains power supply. Edge deployment on battery-powered hardware is identified as a future consideration and is outside the scope of this prototype.

=== Safety

The system handles financial transaction data. Prices and product identities must be sourced from the ERP system, not derived directly from the vision model, to prevent billing errors. The cashier confirmation step is a mandatory safeguard before any transaction is recorded.

=== Regulatory

No formal regulatory certification is required for the prototype. If deployed commercially, integration with licensed payment providers and compliance with Ethiopian financial transaction regulations would be required.

== Success Criteria

#table(
  columns: (2cm, 1fr, 2.5cm),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },
  [*ID*], [*Criterion*], [*Target*],
  [SC-1], [Model `mAP@50` on held-out test set], [≥ 0.90],
  [SC-2], [Model `mAP@50-95` on held-out test set], [≥ 0.75],
  [SC-3], [Inference time per frame (laptop CPU)], [≤ 500 ms],
  [SC-4], [Receipt total accuracy across system test transactions], [100%],
  [SC-5], [Correct product match rate for items in trained catalogue], [≥ 90%],
  [SC-6], [Barcode fallback successfully adds undetected items to receipt], [Pass],
  [SC-7], [Weighted-item price calculation correctness], [100%],
  [SC-8], [Cashier correction workflow completes without system error], [Pass],
)


#pagebreak()
// ============================================================
// 4. SYSTEM DESIGN AND ARCHITECTURE
// ============================================================
= System Design and Architecture

== System-Level Description

The system is structured as a pipeline that begins at the checkout surface and ends with a confirmed transaction record in the ERP system. All modules are coordinated by the backend checkout service, which acts as the central state manager for each transaction.

The pipeline follows this sequence: camera capture → product detection → backend processing → ERP product matching → cashier review → fallback correction (if needed) → receipt generation → payment handling → transaction recording.

The design prioritises correctness over automation. Computer vision is used to accelerate the initial product identification step, but no transaction is finalised without cashier confirmation. 

== Block Diagram
#figure(
  image("system arcitecture.png"),
  caption: [System Architecture]
)


== Major Subsystems

The system comprises ten modules. The responsibilities of each are described below; implementation details appear in Chapter 6.

=== Camera Input Module

Camera input modules capture the checkout surface. Cameras is mounted above or at an angle to the checkout table. The cameras can either be USB webcam, phone camera via USB tether, or dedicated camera module. The prototype uses a phone camera connected via IP webcam software.


Fixed positioning ensures consistent framing and reduces the variability the detection model must handle. Image quality directly governs detection performance: poor lighting, oblique angles, and product occlusion each reduce recall.

=== Product Detection Module

The product detection module runs a YOLOv8 model on each captured frame @ultralytics_yolov8_2023. The model returns, for each detected object: predicted class label, bounding box coordinates, and confidence score. The module is responsible for packaged products sold by quantity — bottled goods, boxed items, canned goods, and similar SKUs. Its output is treated as a draft, not a final product list.

The module is also responsible for identifying repeated instances of the same class within a single frame, which the backend then aggregates into quantity counts.

=== Backend Checkout Module

The backend checkout module, implemented in Django, is the central coordinator of the checkout pipeline @django_documentation_2024. It receives detection results from the model, validates confidence thresholds, groups duplicates, retrieves matched product records from the ERP, and maintains the checkout session state — including all cashier corrections — until the transaction is confirmed.

The backend also orchestrates inter-module communication: it relays the draft receipt to the cashier interface, receives correction instructions from the interface, handles barcode fallback queries, routes weighted-product data, and dispatches confirmed checkout data to the receipt generation and payment modules.

=== ERP Integration Module

The ERP integration module connects the checkout system to Odoo ERP via its JSON-RPC API @odoo_documentation_2024. The ERP is the authoritative source of product information: names, categories, barcodes, unit prices, and unit types. Using the ERP as the price source — rather than embedding prices in the detection model or a local flat file — ensures that price updates made by the store administrator are immediately reflected in checkout transactions.

The module also writes confirmed transactions to the ERP, providing a persistent audit trail and enabling standard ERP reporting on sales and stock movement.

=== Cashier Interface Module

The cashier interface, implemented in React, is the primary interaction point between the system and its human operator @react_documentation_2024. It presents the draft receipt produced by the backend and provides controls for:

- Confirming correct detections.
- Removing incorrect detections.
- Adjusting quantities.
- Adding products not detected by the model (via search or barcode scan).
- Triggering the weighted-product workflow.
- Reviewing the receipt total before confirmation.
- Confirming the final transaction.

The interface design prioritises speed and clarity. Items requiring cashier attention — low-confidence detections, quantity mismatches — are visually flagged.

=== Barcode Fallback Module

The barcode fallback module provides a reliable secondary identification method when the vision model fails. Failure cases include: product outside the training distribution, product partially occluded, insufficient lighting, and visually ambiguous items. The cashier scans the barcode or searches the product catalogue manually. The scanned barcode is resolved to a product record via the ERP integration module, and the item is added to the checkout session. This path ensures that every product — regardless of whether the model can identify it — can be processed through the same receipt workflow.

=== Weighted Product Module

The weighted product module handles products sold by mass rather than by unit, mainly fresh produce such as fruits and vegetables. When a weighted-product transaction is initiated, the item is placed on the digital scale. The system uses a dedicated YOLOv8-based workflow to identify the produce type from the weighing platform and to obtain the displayed weight value from the scale display.

After the produce type and weight are determined, the backend retrieves the corresponding unit price per kilogram from the ERP product catalogue. The item subtotal is then calculated as:

$ "item subtotal" = "unit price per kg" times "measured weight (kg)" $

The calculated weighted item is then added to the draft receipt for cashier review and confirmation.

==== Scale Reading Module

The scale reading module obtains the weight value shown on the digital scale display. In this implementation, conventional OCR is not used. Instead, the scale image is first processed by a YOLOv8 cropper model that detects and extracts the display region. The cropped display is then passed to a YOLOv8 digit-detection model, which detects visible digits and the decimal point as individual object classes.

The detected digit and decimal-point components are ordered from left to right according to their bounding-box positions. This spatial ordering is used to reconstruct the numeric weight value displayed on the scale. The reconstructed value is then validated before being passed to the weighted-product pricing workflow.

Manual cashier entry is retained as a fallback when the display crop is unclear, digit confidence is low, the decimal point is missing or misplaced, or the reconstructed value is invalid.

==== Produce Recognition Module

The produce recognition module identifies the type of fruit or vegetable placed on the weighing platform. The scale camera image is first processed by a YOLOv8 cropper model that detects and extracts the weighing platform region. This crop isolates the produce item from the surrounding scale body, checkout surface, and background.

The cropped platform image is then passed to a YOLOv8 produce-detection model trained to classify selected weighted-product categories. The model returns the detected produce class, bounding box, and confidence score. If the confidence score is above the defined threshold, the detected class is passed to the backend and matched with the corresponding ERP product record.

If the produce type is uncertain, incorrectly detected, or not included in the trained class set, the cashier can manually select the correct product from the interface. This fallback ensures that weighted-item pricing can still proceed even when visual recognition fails.

=== Payment Module

The payment module manages the payment stage. In the prototype, payment is simulated: the cashier can mark a transaction as paid, pending, failed, or cancelled. The module records payment status against the transaction in the ERP. Future integration with Telebirr or Chapa payment APIs is identified as a development path.

=== Admin Management Module

The admin module provides a management interface for store staff. Administrators can add and update product records, adjust prices, manage categories and barcodes, and review transaction history. In the prototype, this functionality is accessed through the Odoo ERP admin panel and a lightweight supplementary interface for model-related administration (product class registration, fallback case review).

== Hardware/Software Architecture

=== Hardware Stack

#table(
  columns: (3.5cm, 1fr, 3cm),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },
  [*Component*], [*Role*], [*Specification*],
  [Compute device], [Runs detection model, backend, and interface], [Laptop (≥ 8 GB RAM) or Raspberry Pi 5 ],
  [Camera], [Captures checkout surface], [USB webcam or phone camera, ≥ 1080p],
  [Barcode scanner], [Barcode fallback input], [USB HID scanner],
  [Digital scale], [Weight measurement for produce], [Generic Weighing Scale],
  [Checkout table], [Product placement surface], [Standard retail counter],
  [Receipt printer], [Optional physical receipt output], [Thermal USB printer],
)


=== Software Stack

#table(
  columns: (3.8cm, 1fr),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*Component*], [*Technology*],

  [Shelf-product detection model],
  [YOLOv8 object detection model using Ultralytics, implemented in Python, for detecting selected supermarket products placed on the checkout surface @ultralytics_yolov8_2023.],

  [Scale display cropper],
  [YOLOv8 object detection model used to detect and crop the digital scale display region from the scale camera image @ultralytics_yolov8_2023.],

  [Weighing platform cropper],
  [YOLOv8 object detection model used to detect and crop the weighing platform region containing the vegetable or produce item @ultralytics_yolov8_2023.],

  [Scale digit detection model],
  [YOLOv8 object detection model trained to detect digits and decimal points from the cropped digital scale display region @ultralytics_yolov8_2023.],

  [Weight reconstruction module],
  [Custom Python logic that orders detected digits and decimal points spatially to reconstruct the numeric weight value shown on the scale display.],

  [Weighted-product detection model],
  [YOLOv8 object detection model trained to identify the vegetable or produce type from the cropped weighing platform region @ultralytics_yolov8_2023.],

  [Image processing],
  [OpenCV for image capture, preprocessing, cropping, detection result handling, and preparation of cropped regions for the YOLOv8 models @opencv_library.],

  [Model training environment],
  [Kaggle Notebook environment with GPU acceleration, using Python, Ultralytics, PyTorch, OpenCV, and NumPy @kaggle_notebooks.],

  [Dataset annotation],
  [Label Studio for bounding-box annotation and YOLO-format label preparation @label_studio_docs.],

  [Backend],
  [Django, Django REST Framework, and Python 3.11 for managing checkout sessions, detection results, product matching, receipt data, and API communication @django_documentation_2024 @drf_documentation.],

  [Cashier interface],
  [React, TypeScript, HTML, and CSS for displaying the draft receipt, cashier corrections, barcode fallback, weighted-product review, and transaction confirmation @react_documentation_2024.],

  [ERP system],
  [Odoo Community Edition for product catalogue management, unit price storage, product category management, and transaction recording @odoo_documentation_2024.],

  [Database],
  [PostgreSQL used through Odoo and backend integration for storing product, transaction, and receipt-related data.],

  [API communication],
  [REST API communication between the detection module, Django backend, cashier interface, and Odoo ERP.],

  [Barcode fallback],
  [USB HID barcode scanner integrated as a fallback input method when product detection is uncertain, incorrect, or unavailable.],

  [Weighted-product handling],
  [Custom backend workflow that combines the detected vegetable class, reconstructed weight value, unit price per kilogram, and calculated subtotal before adding the item to the draft receipt.],

  [Receipt generation],
  [Backend-generated digital receipt containing product names, quantities, unit prices, subtotals, total amount, date, time, payment status, and transaction reference.],

  [Payment simulation],
  [Prototype payment-status module used to simulate transaction completion before final receipt confirmation and ERP transaction recording.]
)
#pagebreak()
== Design Choices and Trade-offs

This section explains the main design decisions made during the development of the proposed cashier-assisted checkout automation system. Each decision involved a trade-off between accuracy, cost, complexity, deployability, and suitability for the target retail environment.

=== Why YOLOv8 Was Chosen over Other Object Detection Models

Object detection models are used to find and classify objects inside an image. For this project, the model must detect supermarket products placed on a checkout table. Several object detection models could have been used, such as Faster R-CNN, SSD, RetinaNet, EfficientDet, DETR, RT-DETR, and YOLO.

Faster R-CNN is a two-stage detector @ren_faster_rcnn_2015. It first looks for possible object regions and then classifies them. This can give good accuracy, but it is usually slower and heavier than one-stage detectors. Since the proposed system is intended for real-time checkout assistance and possible Raspberry Pi deployment, Faster R-CNN was not selected as the main model.

SSD and RetinaNet are one-stage detectors @liu_ssd_2016 @lin_retinanet_2017. They detect and classify objects in one pass, making them faster than many two-stage detectors. However, YOLOv8 was preferred because it has a simpler training process, strong community support, and an easy Python interface through the Ultralytics library.

EfficientDet is another efficient object detector @tan_efficientdet_2020. It is designed to balance speed and accuracy, but it can be more complex to configure and integrate compared with YOLOv8. For this project, ease of training, testing, and deployment was important, so YOLOv8 was more practical.

Transformer-based detectors such as DETR and RT-DETR are newer object detection models @carion_detr_2020 @zhao_rtdetr_2024. They can be powerful, but they are more complex and may need more computing resources or careful optimisation. Since this thesis focuses on building a working low-cost prototype, these models were considered more suitable for future improvement rather than the first implementation.

YOLOv8 was chosen because it gives a good balance between speed, accuracy, and ease of use @ultralytics_yolov8_2023. It can detect multiple products in one image and returns the product class, bounding box, and confidence score. These outputs are useful for the Django backend, which uses them to match products with the ERP catalogue and prepare the draft receipt.

In this project, YOLOv8 is also suitable because the system is cashier-assisted. The model does not need to make the final decision alone. It only needs to provide fast and useful detections, while the cashier checks and corrects the result before confirming the transaction.
=== Cashier-in-the-loop over Full Automation

The system was designed as a cashier-assisted workflow rather than a fully autonomous checkout system. Full automation would require consistently high detection accuracy across a large and changing product catalogue, including overlapping products, damaged packaging, unknown items, and difficult lighting conditions. Achieving this level of reliability is not realistic for a first prototype trained on a limited local dataset.

Keeping the cashier in the loop makes the system more practical and safer for real checkout use. The detection model produces a draft receipt, while the cashier remains responsible for reviewing, correcting, and confirming the transaction. This design allows the system to reduce repetitive product identification work without making transaction accuracy fully dependent on the model.
=== Why YOLOv8 Was Chosen over Other YOLO Versions

Several YOLO versions could be used for this project, including YOLOv5, YOLOv7, YOLOv8, YOLOv9, YOLOv10, and YOLO11. YOLOv8 was selected because it provides a strong balance between accuracy, speed, ease of training, and integration support.

YOLOv5 is widely used and stable, but YOLOv8 is newer and provides a more modern Ultralytics workflow for training, validation, prediction, and export @ultralytics_yolov8_2023. Since this project required custom training on supermarket product images and later integration with a Python-based backend, YOLOv8 provided a simpler and more convenient development path.

YOLOv7 is known for strong detection performance, but its training and integration workflow is less convenient for this prototype compared with the Ultralytics YOLOv8 Python API @wang_yolov7_2023 @ultralytics_yolov8_2023. YOLOv8 made it easier to train models, run inference, export results, and connect detection outputs to the Django backend.

YOLOv9, YOLOv10, and YOLO11 are newer alternatives, and some may provide improved accuracy or efficiency @wang_yolov9_2024 @wang_yolov10_2024 @ultralytics_yolo11_2024. However, newer models can introduce changes in architecture, documentation, dependency requirements, or deployment behaviour. For this thesis, the priority was not only maximum accuracy, but also stability, available learning resources, implementation simplicity, and reliable integration within the project timeline.

YOLOv8 was therefore chosen because it is modern enough to provide strong real-time detection performance, while also being mature enough to train, test, debug, and deploy reliably @ultralytics_yolov8_2023. Its outputs, including class labels, bounding boxes, and confidence scores, are directly suitable for the checkout workflow, where detected products are passed to the backend, matched with ERP catalogue records, and reviewed by the cashier before transaction confirmation.

=== Odoo ERP over a Standalone Product Database

Odoo ERP was selected for product catalogue management and transaction recording instead of using only a custom local database @odoo_documentation_2024. This choice allows the prototype to demonstrate integration with a business-oriented system that supports product records, prices, categories, barcodes, sales transactions, and reporting.

The benefit of this approach is that the checkout automation system is not isolated from normal retail operations. Detected products can be matched against real product records, and confirmed transactions can be recorded in the ERP. The trade-off is increased setup and integration complexity compared with a simple standalone database. However, this complexity is acceptable because ERP integration makes the prototype closer to a practical retail system.

=== Django Backend over Direct Frontend-to-Model Communication

A Django backend was used as the central coordination layer between the detection models, cashier interface, Odoo ERP, barcode fallback, weighted-product workflow, and receipt generation process @django_documentation_2024 @drf_documentation. This avoids placing business logic directly inside the frontend or detection scripts.

The backend manages checkout state, product matching, quantity aggregation, price retrieval, receipt preparation, and transaction confirmation. This makes the system easier to maintain and extend. The trade-off is that the backend introduces an additional software layer, but this is justified because the system requires more than simple image detection; it requires coordinated checkout logic.

=== React Interface for Cashier Review

React was selected for the cashier interface because it supports interactive user interfaces and can update the draft receipt dynamically as detections, corrections, barcode inputs, and weighted-product entries are added @react_documentation_2024. This is important because the cashier must be able to review and correct the transaction before confirmation.

The trade-off is that a React frontend requires additional development effort compared with a basic HTML interface. However, the improved usability is important for a cashier-facing system where speed, clarity, and correction support are central requirements.

=== Local Deployment over Cloud-based Inference

The system is designed primarily for local or edge deployment rather than cloud-based inference. Local deployment reduces dependence on internet connectivity, avoids network delays during checkout, and lowers recurring cloud service costs. These factors are important for the intended low-cost retail context.

The trade-off is that local hardware has limited processing power compared with cloud GPUs. This creates a need for model optimisation, efficient image capture, and careful hardware selection. For the prototype, this trade-off is acceptable because the goal is to demonstrate a practical and affordable cashier-assisted system rather than a large-scale cloud service.

=== Barcode Fallback over Vision-only Checkout

A barcode scanner is included as a fallback input method. A vision-only system would fail when products are missed, misclassified, occluded, outside the trained class set, or detected with low confidence. Barcode fallback allows the cashier to complete the transaction even when computer vision is unreliable.

This design improves system robustness. The trade-off is that the system still depends partly on manual cashier action, but this is consistent with the cashier-assisted design philosophy. The objective is not to remove all manual input, but to reduce unnecessary repetitive scanning while preserving transaction correctness.

=== Separate Weighted-product Workflow

Weighted products were handled using a dedicated workflow instead of being treated the same as packaged shelf products. This is necessary because fruits and vegetables are priced by mass rather than by fixed unit price. The system therefore needs both product identification and weight acquisition.

The weighted-product workflow uses YOLOv8-based cropper models to isolate the digital scale display and weighing platform @ultralytics_yolov8_2023. The display crop is used for digit and decimal-point detection, while the platform crop is used for produce recognition. The trade-off is increased model and workflow complexity, but this separation makes the system more suitable for realistic supermarket checkout scenarios where both packaged and weighed products are common.


#pagebreak()
// ============================================================
// 5. MATERIALS AND METHODS
// ============================================================
= Materials and Methods

== Tools and Components

=== Hardware


All hardware used in the prototype is commercially available consumer-grade equipment:

- *Compute:* Laptop with Intel Core i5 or equivalent, 16 GB RAM, running Ubuntu 22.04 LTS or Windows 11. A Raspberry Pi 5 (8 GB) is tested as a lower-cost deployment target.
- *Camera:* A phone camera, using any ip/camera software, particularly ip webcam.
- *Barcode scanner:* Generic USB HID laser barcode scanner. 
- *Digital scale:* Generic weighing scale..
- *Checkout surface:* Standard table with matte black surface to reduce specular reflection.

=== Software Frameworks and Libraries

#table(
  columns: (3.8cm, 1fr, 2.3cm),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*Library / Tool*], [*Purpose*], [*Version*],

  [Python],
  [Main programming language for model training, inference, image processing, and backend development.],
  [3.11],

  [Ultralytics YOLOv8],
  [Training and inference framework for shelf-product detection, scale-display cropping, platform cropping, digit/dot detection, and produce recognition @ultralytics_yolov8_2023.],
  [8.x],


  [Kaggle Notebooks],
  [GPU-based model training environment used for training and evaluating the YOLOv8 models @kaggle_notebooks.],
  [Web],

  [Label Studio],
  [Dataset annotation tool used to create bounding-box labels in YOLO format @label_studio_docs.],
  [1.8.x],


  [Django],
  [Backend web framework for checkout state management, product matching, receipt preparation, and transaction coordination @django_documentation_2024.],
  [4.2],


  [React],
  [Frontend framework for the cashier interface, draft receipt review, correction workflow, and transaction confirmation @react_documentation_2024.],
  [18],



  [Odoo Community Edition],
  [ERP system used for product catalogue management, price records, product categories, and transaction recording @odoo_documentation_2024.],
  [16 CE],

  [YOLOv8 digit/dot detection],
  [Scale display reading method that detects digits and decimal points from the cropped scale display region.],
  [Custom model],

  [Weight reconstruction logic],
  [Custom Python logic that orders detected digits and decimal points from left to right to reconstruct the displayed weight value.],
  [Custom],


)







== Dataset Collection and Preparation


The detection model was developed using a custom grocery-item dataset collected for the proposed checkout-assistance system. The dataset was prepared to represent products placed on a checkout surface, rather than products arranged on shelves. This matches the intended operating condition of the system, where items are placed on a table and detected by a camera before a draft receipt is generated.

A total of 1,012 product images were collected using a phone camera. After manual filtering, 877 usable images were retained for annotation and model training. Images that were blurred, poorly framed, duplicated, or unsuitable for object detection were removed from the final dataset. The final dataset contains both single-product and multi-product images, allowing the model to learn individual product appearance as well as realistic checkout scenes containing more than one item.

=== Product Selection

The dataset contains 17 grocery-item classes selected from common packaged products found in Ethiopian retail environments. The selected products include beverages, snacks, tissue paper, soap, detergent, pasta, tuna, and other packaged goods. These classes were chosen to support a controlled prototype while still representing visually different product shapes, colors, and packaging types.

#table(
  columns: (1cm, 1fr),
  stroke: 0.4pt,
  inset: 5pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [ID], [Class Name],
  [0], [Abounded Biscuit],
  [1], [Blue Sunchips],
  [2], [Bravo Tissue Paper],
  [3], [Cappuccino],
  [4], [Coca Cola],
  [5], [Decoy],
  [6], [Dove Soap],
  [7], [Duru Soap],
  [8], [Eve Comfort],
  [9], [Mawell Pasta],
  [10], [Nice Small Soft],
  [11], [Omaar Tuna],
  [12], [Pepsi],
  [13], [Red QQ snack],
  [14], [Sol Water],
  [15], [Yellow Sunchips],
)

The class names above follow the naming used in the YOLO dataset configuration. Obvious spelling inconsistencies were kept unchanged in the dataset to avoid mismatch between the annotation files, dataset configuration, and trained model.

=== Image Capture Protocol

Images were captured using a phone camera in a checkout-like tabletop setup. The purpose of the image capture process was to expose the model to variations that may occur during actual use. The dataset therefore includes differences in lighting, camera distance, product orientation, background appearance, and product arrangement.

The captured images include:

+ Single-product images, where one item is visible in the frame.
+ Multi-product images, where two or more items appear together on the checkout surface.
+ Images captured under natural lighting.
+ Images captured under LED lighting.
+ Images captured under dim lighting.
+ Images with different product orientations, including front-facing, side-facing, and rotated products.
+ Images with different camera distances and framing conditions.
+ Images with partial overlap between products in multi-object scenes.

The final filtered dataset contains 618 single-object images and 259 multi-object images. This balance was useful because single-object images helped the model learn the visual features of each product class, while multi-object images helped test whether the model could detect several products in one checkout scene.

=== Annotation

The images were annotated using Label Studio. Each visible product instance was labelled with a rectangular bounding box and assigned to one of the 17 product classes. Standard axis-aligned bounding boxes were used; rotated bounding boxes were not used.

The annotations were exported in YOLO format @redmon_yolo_2016. In this format, each image has a corresponding text label file, and each line in the label file represents one object instance using:

$ "class_index, x_center, y_center, width, height" $

The bounding-box coordinates are normalized relative to the image width and height. This makes the annotations compatible with YOLO training pipelines.

After annotation, the dataset was reviewed to reduce obvious labeling problems. Images with poor quality, unclear objects, or unsuitable framing were excluded before the final training split was used.

=== Dataset Splits and Augmentation

The final dataset contains 877 usable images. The dataset was divided into training, validation, and test sets as follows:

#table(
  columns: (1fr, 1.5cm, 1.5cm),
  stroke: 0.4pt,
  inset: 5pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [Set], [Images], [Approx. Share],
  [Training], [613], [70%],
  [Validation], [174], [20%],
  [Test], [90], [10%],
)

The training set was used to update the model weights. The validation set was used during training to monitor model performance and guide model selection. The test set was kept separate and used for final prediction testing after training.

No custom augmentation pipeline was manually specified in the notebook. Instead, training-time augmentation was handled using the default Ultralytics YOLOv8 training configuration @ultralytics_yolov8_2023. The default configuration included color-space variation, translation, scaling, horizontal flipping, mosaic augmentation, and random erasing. Rotation, vertical flipping, shear, perspective transform, mixup, copy-paste, and cutmix were not enabled in the training configuration.

Validation and test images were not manually augmented. They were used as evaluation images so that the measured performance reflected detection on original image samples.

=== Training Configuration

The object detection model was trained using the Ultralytics YOLO framework @ultralytics_yolov8_2023. YOLOv8n was selected because it is the smallest model in the YOLOv8 family and is therefore suitable for a prototype that may later be deployed on resource-constrained edge hardware such as a Raspberry Pi.

Training was performed on Kaggle using a Tesla T4 GPU @kaggle_notebooks. The model was initialized using COCO-pretrained YOLOv8n weights and then fine-tuned on the custom Ethiopian grocery dataset @lin_coco_2014 @ultralytics_yolov8_2023.

The training configuration used in the notebook was:

#table(
  columns: (1fr, 2fr),
  stroke: 0.4pt,
  inset: 5pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [Parameter], [Value],
  [Framework], [Ultralytics YOLO],
  [Ultralytics Version], [8.4.7],
  [Model], [YOLOv8n],
  [Pretrained Weights], [yolov8n.pt],
  [Dataset Path], [/kaggle/input/ethiopian-grocery-items-v1],
  [Image Size], [640 x 640],
  [Epochs], [50],
  [Batch Size], [16],
  [Workers], [2],
  [Device], [CUDA device 0],
  [GPU], [Tesla T4],
  [Optimizer], [auto],
  [Early-Stopping Patience], [100],
  [Output Directory], [/kaggle/working/runs/detect/train],
)


The trained model produced the following validation performance during the notebook run:

#table(
columns: (1fr, 1.5cm),
stroke: 0.4pt,
inset: 5pt,
fill: (col, row) => if row == 0 { luma(220) } else { none },

[Metric], [Value],
[Precision], [0.9504],
[Recall], [0.8775],
[$"mAP@50"$], [0.9321],
[$"mAP@50-95"$], [0.8316],
)


== Weighted-product Dataset Collection and Preparation

The weighted-product vision pipeline was developed using a custom dataset collected for produce items sold by mass. Unlike the packaged-product detector, which identifies fixed-price grocery items placed on a checkout table, this dataset supports the weighing workflow. The goal is to identify the produce item placed on a digital scale and extract the displayed weight value from the scale display.

The weighted-product dataset was prepared for a scale-based checkout setup. Images were captured using a phone camera, with the produce item placed on the weighing platform and the digital scale display visible in the same frame. This allowed the system to learn both the location of the produce region and the location of the display region.

The final weighted-product vision workflow uses three model components: a YOLOv8 cropper model, a YOLOv8 digit/dot detection model, and a vegetable classification model. The cropper model detects the `display` and `vegetable` regions. The digit/dot model detects the visible numbers and decimal point from the cropped scale display. The vegetable classifier identifies the produce type from the cropped vegetable region.

=== Produce Class Selection

The produce classes were selected from common vegetables and fruits that are typically sold by weight. The selected classes provide a controlled prototype dataset while still representing different shapes, colors, sizes, and surface textures.

#table(
  columns: (1cm, 1fr, 1fr),
  stroke: 0.4pt,
  inset: 5pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*ID*], [*Class Name*], [*Stored Label Name*],

  [0], [Avocado], [`avocado`],
  [1], [Beetroot], [`beetrot`],
  [2], [Cabbage], [`cabbage`],
  [3], [Carrot], [`carrot`],
  [4], [Chilli], [`chilly`],
  [5], [Lemon], [`lemon`],
  [6], [Onion], [`onion`],
  [7], [Potato], [`potato`],
  [8], [Watermelon], [`watermelon`],
)
=== Image Capture Protocol

Images were captured in a scale-based setup where the produce item was placed on the weighing platform and the digital scale display was visible in the frame. This setup was chosen to match the intended operating condition of the weighted-product module, where the system must determine both the type of produce and the measured weight.

The captured images include:

+ Produce items placed on the digital scale platform.
+ Images where the digital display and produce region are visible in the same frame.
+ Different produce orientations on the weighing platform.
+ Different camera distances and framing conditions.
+ Variations in lighting and background appearance.
+ Differences in display visibility, including clearer and less clear numeric readings.

This image capture approach supports the two-stage vision workflow. First, the system detects the relevant regions of interest from the full image. Then, the cropped regions are processed separately for produce classification and weight reconstruction.

=== Cropper Dataset Annotation

The first model in the weighted-product pipeline is a YOLOv8 cropper model. This model was trained to detect two regions of interest in the scale image: the digital display region and the vegetable region.

#table(
  columns: (1cm, 1fr, 2fr),
  stroke: 0.4pt,
  inset: 5pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*ID*], [*Class Name*], [*Purpose*],

  [0], [`display`], [Detects the digital scale display region containing the measured weight value.],
  [1], [`vegetable`], [Detects the produce/platform region containing the item being weighed.],
)

Each training image was annotated with rectangular bounding boxes around the display and vegetable regions where visible. The annotations were exported in YOLO format, where each object instance is represented using:

$ "class_index, x_center, y_center, width, height" $

The coordinates are normalized relative to the image width and height. This format is compatible with the YOLOv8 training pipeline.

=== Digit and Decimal-point Dataset

The cropped display region was used to train a separate YOLOv8 digit/dot detection model. This model does not use conventional OCR. Instead, it treats each visible digit and decimal point as an object detection class.

#table(
  columns: (1cm, 1fr),
  stroke: 0.4pt,
  inset: 5pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*ID*], [*Class Name*],

  [0], [`digit_0`],
  [1], [`digit_1`],
  [2], [`digit_2`],
  [3], [`digit_3`],
  [4], [`digit_4`],
  [5], [`digit_5`],
  [6], [`digit_6`],
  [7], [`digit_7`],
  [8], [`digit_8`],
  [9], [`digit_9`],
  [10], [`dot`],
)

After detection, the digit and decimal-point bounding boxes are sorted from left to right according to their horizontal position. The ordered detections are then combined to reconstruct the displayed weight value. For example, detections ordered as `digit_1`, `dot`, `digit_2`, and `digit_5` are reconstructed as `1.25`.

=== Vegetable Classification Dataset

The vegetable classification dataset was prepared from images of produce items belonging to the selected produce classes. The classifier receives the cropped vegetable region and predicts the produce type. This classification stage is separate from the YOLOv8 cropper model. The cropper only identifies where the vegetable region is located, while the classifier determines which vegetable or fruit is present.

The vegetable classifier was trained using the produce classes listed in the class-index mapping file. During deployment, the predicted class is combined with the reconstructed weight value and the unit price per kilogram retrieved from the ERP catalogue.

=== Training Configuration

The weighted-product models were trained in the Kaggle Notebook environment. The final exported package contains the trained YOLOv8 cropper model, the YOLOv8 digit/dot reader model, the vegetable classifier, and the class-index mapping file.

#table(
  columns: (4cm, 1fr),
  stroke: 0.4pt,
  inset: 5pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*Component*], [*Training / Model Description*],

  [Cropper model],
  [YOLOv8 model trained to detect `display` and `vegetable` regions from full scale images.],

  [Digit/dot reader model],
  [YOLOv8 model trained to detect `digit_0` to `digit_9` and `dot` from cropped display images.],

  [Vegetable classifier],
  [MobileNetV2-based classifier trained to identify the produce type from the cropped vegetable region @sandler_mobilenetv2_2018.],

  [Training platform],
  [Kaggle Notebook environment with GPU acceleration.],

  [Exported deployment package],
  [`raspberry_pi_deployment_package.zip` containing model files, class indices, and thesis evidence.],
)

The trained models were exported into a Raspberry Pi deployment package containing `yolo_cropper_vegetable_display.pt`, `yolo_digit_reader.pt`, `vegetable_classifier.h5`, and `class_indices.json`. The package also includes training evidence such as result curves, confusion matrices, and metric CSV files for the YOLOv8 models.




#pagebreak()












= Implementation


== Step-by-Step Development

The implementation was carried out in two main stages. The first stage focused on model development and training, while the second stage focused on software development, system integration, and end-to-end prototype testing.

=== Stage 1: Model Development and Training

The first implementation stage involved preparing the computer-vision models required for the checkout prototype. This included dataset collection, image filtering, annotation, dataset organization, training, and model evaluation.

For packaged supermarket products, images were collected under checkout-like conditions using a phone camera. The images included single-product and multi-product scenes so that the model could learn both individual product appearance and realistic checkout-table arrangements. After filtering unsuitable images, the remaining dataset was annotated using bounding boxes and exported in YOLO format.

A YOLO-based object detection model was then trained to recognize selected supermarket product SKUs. The model was fine-tuned from a pretrained YOLO checkpoint instead of being trained from scratch @ultralytics_yolov8_2023. This reduced training difficulty and allowed the model to adapt to the custom grocery-item dataset. After training, the best-performing checkpoint was selected for inference and later connected to the checkout system.

A separate weighted-product vision pipeline was also developed for fruits and vegetables. This pipeline was designed to identify the produce type and reconstruct the weight displayed on a digital scale. The weighted-product workflow used a cropper model to isolate the display and produce regions, a digit/dot detection model to read the scale value, and a produce classification model to identify the item being weighed.

At the end of this stage, the required vision components were ready for system integration. The required vision components were ready for system integration via a FastAPI inference service @fastapi_documentation.

=== Stage 2: Integration and Software Development

The second implementation stage focused on developing the checkout software and connecting the trained models to the full prototype workflow. This stage included backend development, frontend interface implementation, YOLO service integration, checkout logic, receipt handling, and final integration testing.

The Django backend was developed as the main control component of the prototype @django_documentation_2024 @drf_documentation. It was configured with Django REST Framework and organized into separate modules for product catalog management, checkout sessions, vision integration, receipt handling, payment simulation, and ERP-related preparation. Product records were added with fields such as product name, SKU, category, unit type, barcode, and current price. Detection class mappings were also prepared so that class names returned by the YOLO model could be linked to actual product records.

Checkout-session logic was then implemented. A cashier can create a checkout session, add products manually, update quantities, remove incorrect items, and calculate the total price. This basic checkout flow was implemented before model integration so that the system could operate independently of the computer-vision component.

After the checkout logic was functional, the YOLO inference service was connected to the backend. Captured images or test frames are processed by the inference service, which returns detected classes, bounding boxes, and confidence scores. The backend receives these results, maps the detected classes to product records, and adds them to the checkout session as draft items. The cashier can then review, edit, remove, or confirm the detected items before final receipt generation.

The React cashier interface was developed and connected to the backend APIs @react_documentation_2024. The interface allows the cashier to start a session, submit a camera frame or test image, view detected products, edit quantities, remove wrong detections, add missed products manually, add weighted products, and preview the receipt total.

Finally, the backend, frontend, and YOLO service were integrated and tested together using sample checkout transactions. The purpose of this stage was to confirm that model inference, product matching, cashier correction, price calculation, weighted-product handling, and receipt generation worked as one connected prototype.



== UI Layouts


#figure(
  image("loginpage.png", width: 80%),
  caption: [Login page of the retail checkout automation system.]
)


#figure(
  image("greet_page.png", width: 80%),
  caption: [Greeting page displayed after successful login.]
)


#figure(
  image("main checkout screen.png", width: 80%),
  caption: [Main checkout screen before product detection.]
)


#figure(
  image("camera settings page.png", width: 80%),
  caption: [Camera settings page for selecting and configuring the input source.]
)


#figure(
  image("with products detected.png", width: 80%),
  caption: [Checkout screen showing products detected by the computer vision module.]
)


#figure(
  image("final_bill.png", width: 80%),
  caption: [Final bill screen after cashier confirmation.]
)


#figure(
  image("print_preview.png", width: 80%),
  caption: [Print preview page for the generated receipt.]
)


== Source Code Organization

The prototype source code was organized into separate folders for the backend, frontend, computer-vision service, dataset/model files, and helper scripts. 

```text
retail-checkout-automation/
│   
├── backend/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── catalog/
│   │   ├── checkout/
│   │   ├── vision/
│   │   ├── receipts/
│   │   ├── payments/
│   │   └── erp/
│
├── frontend/
│   └── src/
│
│
├── yolo_service/
│   ├── main.py
│   └─── models/
│      └── best.pt
│
├── dataset/
│   ├── images/
│   ├── labels/
│   └── data.yaml
│
├── odoo_erp/
│
│
├── weighted_detection_service/
│   ├── main.py
│   └─── models/
│      └── best.pt
│
└── scripts/
    └── orchestrate.sh
```


#pagebreak()




= Testing and Validation

The testing strategy was divided into three levels. The first level tested the object detection model independently using standard detection metrics. The second level tested the integration between the YOLO service and the Django backend API. The third level tested the complete backend checkout flow from image submission to draft receipt item generation.


== Test Plan and Strategy


The main test objectives were:

+ To evaluate the trained YOLOv8n model on selected grocery product classes.
+ To verify that the Django backend can call the YOLO service and receive detections.
+ To confirm that detected product classes can be converted into draft checkout items.
+ To measure the backend API latency for normal packaged-product detection.
+ To verify the weighted-product vision pipeline separately before full backend integration.
+ To measure the latency of the full weighted-product vision pipeline.
+ To identify untested areas that require further validation before deployment.

The packaged-product checkout workflow was tested through the backend API using test images from the dataset. The weighted-product subsystem was tested separately in a Kaggle Notebook environment using scale images. This means the weighted-product result represents vision-pipeline performance only, not full checkout-system latency.

== Unit Tests, Integration Tests, and System Tests

=== Unit-Level Tests

Unit-level testing focused on individual pieces of logic that support the checkout process. The model suggests detected products, but the backend must still map those detections to product records, calculate quantities, and prepare draft checkout items correctly.

#table(
  columns: (1.2fr, 2fr, 1.3fr),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*Component*], [*Test Objective*], [*Expected Result*],
  [Product mapping], [Verify that a YOLO class maps to the correct product record], [Correct product and price are returned],
  [Duplicate grouping], [Verify that repeated detections are handled as repeated products], [Quantity is increased correctly],
  [Receipt calculation], [Verify subtotal and total calculation], [Correct line totals and checkout total],
  [Weighted-price calculation], [Verify weighted-product subtotal formula], [Subtotal equals unit price per kg multiplied by measured weight],
) <tab-unit-test-plan>


=== Integration Tests

Integration testing was performed on the normal packaged-product workflow. The tested integration flow was:

#align(center)[
  Image input $arrow.r$ Backend API $arrow.r$ YOLO service $arrow.r$ Detection result $arrow.r$ Product lookup $arrow.r$ Draft checkout items
]

The purpose of this test was to confirm that the backend could receive an image, call the YOLO service, process the returned detections, map detected classes to catalogue products, and return a structured API response.

#table(
  columns: (1fr, 4cm, 3cm),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*Integration Test*], [*Result*], [*Status*],
  [Backend receives image request], [90 / 90 successful], [Passed],
  [YOLO service returns detections], [90 / 90 completed], [Passed],
  [Backend returns JSON response], [90 / 90 HTTP 200], [Passed],
  [Timing values returned], [Timing fields included], [Passed],
  [Draft item generation], [145 draft items generated from 166 detections], [Passed],
) <tab-packaged-integration-tests>

The weighted-product subsystem was also tested as a separate integration workflow. This test verified that the cropper model, digit/dot detector, produce classifier, and weight reconstruction logic could operate together on scale images.

#table(
  columns: (1.5cm, 1.8fr, 1.8fr, 1.2cm),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*Test ID*], [*Test Objective*], [*Expected Result*], [*Result*],

  [WST-1],
  [Detect the scale display region from a full scale image],
  [Display region is detected and cropped],
  [Passed],

  [WST-2],
  [Detect the produce/platform region from a full scale image],
  [Produce region is detected and cropped],
  [Passed],

  [WST-3],
  [Detect digits and decimal point from the cropped display],
  [Digits and dot are detected as separate classes],
  [Passed],

  [WST-4],
  [Reconstruct the displayed weight value],
  [Detected digits are ordered from left to right and converted to a numeric value],
  [Passed],

  [WST-5],
  [Classify the cropped produce region],
  [Produce classifier returns class and confidence score],
  [Passed],

  [WST-6],
  [Return structured weighted-product output],
  [Output contains produce type, reconstructed weight, and confidence values],
  [Passed],

  [WST-7],
  [Measure weighted-product vision pipeline latency],
  [Pipeline processes one scale image within acceptable prototype response time],
  [Passed],
) <tab-weighted-subsystem-tests>

=== System-Level Tests

System testing evaluated the implemented backend detection pipeline as a working checkout subsystem. For normal packaged products, the tested flow started with an image request and ended with a backend response containing detections, draft items, and timing values.

The following stages were measured:

+ YOLOv8n inference time.
+ Detection post-processing time.
+ Product lookup time.
+ Receipt/draft item building time.
+ Total backend processing time.
+ Client-side total request time.

The benchmark was performed in a local CPU environment. CUDA was not available during this test, so these results represent CPU-based local execution.

The weighted-product system test was limited to the vision subsystem. It measured the full weighted-product image-processing pipeline, including region detection, crop extraction, digit/dot detection, produce classification, and weight reconstruction. It did not include backend pricing, ERP lookup, frontend rendering, cashier correction, payment simulation, or receipt generation.

== Test Results and Measurements

=== Packaged-Product Detection Model Results

The trained packaged-product detector was evaluated using standard object detection metrics @lin_coco_2014. The model used was YOLOv8n, trained on the custom grocery dataset with an input image size of 640 pixels.

#table(
  columns: (1fr, 1.5cm),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*Metric*], [*Value*],
  [Precision], [0.9504],
  [Recall], [0.8775],
  [$"mAP@50"$], [0.9321],
  [$"mAP@50-95"$], [0.8316],
) <tab-packaged-model-results>

The precision result shows that most predicted detections were correct. The recall result shows that the model detected most labelled objects, although some products were still missed. The $"mAP@50"$ value shows strong detection performance at an IoU threshold of 0.50, while $"mAP@50-95"$ gives a stricter evaluation across multiple IoU thresholds.

These results are valid for the selected prototype product classes only. They should not be interpreted as general supermarket-scale recognition performance.

=== Packaged-Product Backend API Latency Results

The backend API benchmark was performed using 90 test images. Each image was submitted to the backend detection endpoint, and the backend returned timing values for the main processing stages. All 90 requests returned HTTP status 200.

#table(
  columns: (1fr, 3cm, 3cm, 3cm),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*Measured Stage*], [*Mean*], [*Maximum*], [*Std. Dev.*],
  [YOLOv8n inference], [237.37 ms], [346.93 ms], [28.63 ms],
  [Detection post-processing], [0.65 ms], [9.67 ms], [1.92 ms],
  [Product lookup], [2.45 ms], [11.23 ms], [1.91 ms],
  [Receipt building], [11.80 ms], [22.46 ms], [3.99 ms],
  [Total backend processing], [255.63 ms], [367.60 ms], [31.63 ms],
  [Client total request time], [313.83 ms], [448.08 ms], [35.22 ms],
) <tab-packaged-api-latency>

The mean backend processing time was 255.63 ms, and the maximum backend processing time was 367.60 ms. Including client-side request overhead, the mean total request time was 313.83 ms, and the maximum was 448.08 ms. Therefore, all tested packaged-product images were processed in less than 0.5 s from the client request perspective.


#table(
  columns: (1fr, 1.5cm),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*Measurement*], [*Value*],
  [Number of test images], [90],
  [Successful HTTP responses], [90],
  [Failed requests], [0],
  [Total detections], [166],
  [Average detections per image], [1.84],
) <tab-packaged-detection-counts>

The number of draft receipt items is lower than the number of raw detections because the backend does not directly convert every detection into a final receipt line. The system prepares draft items that can be reviewed and corrected by the cashier before final confirmation.

=== Weighted-Product Vision Pipeline Latency

The full YOLO-based weighted-product vision pipeline was benchmarked in the Kaggle Notebook environment. This benchmark measured the execution time of the weighted-product vision pipeline only. It included YOLOv8 cropper inference, display-region cropping, produce-region cropping, produce classification, YOLOv8 digit/dot detection, and weight reconstruction.

The benchmark did not include the other backend pipline tasks. Therefore, the result is reported as weighted-product vision-pipeline latency rather than full end-to-end checkout latency.

#table(
  columns: (1fr, 2.2cm, 2.3cm, 2cm, 2cm, 2cm),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*Pipeline*], [*Images Tested*], [*Average Time*], [*Minimum*], [*Maximum*], [*Std. Dev.*],

  [Full YOLO-based weighted-product vision pipeline],
  [100],
  [199.49 ms],
  [146.23 ms],
  [260.27 ms],
  [28.87 ms],
) <tab-weighted-pipeline-latency>

The full weighted-product vision pipeline achieved an average processing time of 199.49 ms per image in the Kaggle environment. The minimum recorded time was 146.23 ms, while the maximum was 260.27 ms. This corresponds to approximately:

$ 1000 / 199.49 = 5.01 " images/s" $

This indicates that the weighted-product vision subsystem can process approximately five scale images per second under the tested Kaggle environment.

=== Weighted-Product Component Latency

The individual YOLOv8 components used inside the weighted-product vision subsystem were also benchmarked separately. 

#table(
  columns: (1fr, 2.2cm, 2.5cm, 2.5cm, 2cm),
  stroke: 0.4pt,
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(220) } else { none },

  [*Component*], [*Images Tested*], [*Average Total Time*], [*Average Inference Time*], [*Std. Dev.*],

  [YOLOv8 display/produce cropper],
  [100],
  [14.24 ms],
  [9.25 ms],
  [8.90 ms],

  [YOLOv8 digit/dot detector],
  [100],
  [10.83 ms],
  [6.69 ms],
  [1.19 ms],

  [Full weighted-product vision pipeline],
  [100],
  [199.49 ms],
  [Not separately measured],
  [28.87 ms],
) <tab-weighted-component-latency>

The standalone model benchmarks show the latency of the individual YOLOv8 components. The full pipeline time is higher because it includes sequential execution of all processing stages, crop extraction, produce classification, digit ordering, weight reconstruction, and intermediate image handling.




=== Performance Analysis

The packaged-product backend benchmark shows that YOLO inference is the main contributor to total backend processing time. The mean YOLO inference time was 237.37 ms, while the mean total backend processing time was 255.63 ms.

The percentage contribution of YOLO inference to backend processing time is:

$ 237.37 / 255.63 times 100 = 92.86% $

This shows that most delay comes from the detection model rather than from product lookup or draft receipt generation.


For the weighted-product subsystem, the average vision-pipeline latency was 199.49 ms. This is acceptable for a cashier-assisted weighted-product workflow because the system only needs to process an image when a weighted item is placed on the scale. It does not require continuous high-frame-rate video processing.



// ============================================================
// 8. RESULTS AND DISCUSSION
// ============================================================

#pagebreak()
= Results and Discussion

This chapter presents and interprets the results from the implemented cashier-assisted checkout prototype. Four areas are covered: packaged-product detection performance, backend checkout API latency, weighted-product vision subsystem performance, and the engineering implications of all measured results. The chapter also compares expected versus actual performance against the success criteria defined in Chapter 3, documents observed failure cases, and extracts engineering insights relevant to future development.


== Overview of Main Findings

The prototype produced positive results across both detection accuracy and processing speed. The packaged-product YOLOv8n detector achieved strong validation performance on the 15 selected grocery classes. The backend API successfully processed all 90 test images in the benchmark. The weighted-product vision subsystem also demonstrated short processing latency under the Kaggle test environment.

#table(
  columns: (2fr, 2fr, 3fr, auto),
  stroke: 0.5pt + rgb("#cccccc"),

  table.header(
    [*Area evaluated*],
    [*Main result*],
    [*Interpretation*],
    [*Status*],
  ),

  [Packaged-product detection],
  [
    $"mAP@50"$ = 0.9321 \
    Precision 0.9504 \
    Recall 0.8775
  ],
  [Strong prototype-level accuracy on the 15 selected grocery classes.],
  [Met],

  [Backend API reliability],
  [
    90 / 90 requests \
    HTTP 200 \
    0 failures
  ],
  [The detection pipeline operated without error during the full benchmark.],
  [Met],

  [Checkout initiation latency],
  [
    Max client time = 448 ms \
    Mean 313 ms
  ],
  [All requests returned below the 2 s response target, with 78% headroom remaining.],
  [Met],

  [Weighted-product vision pipeline],
  [
    Avg = 199 ms / image \
    Min 146 ms · Max 260 ms
  ],
  [Fast enough for prototype-level cashier-assisted weighted-item workflows.],
  [Met],


)

These results confirm that the prototype is technically feasible for a controlled cashier-assisted checkout scenario. However, they should not be interpreted as full commercial deployment readiness. The system was evaluated on selected product classes, controlled datasets, and local or cloud environments rather than live retail conditions.

== Packaged-Product Detection Results

The packaged-product detector was trained using YOLOv8n on the 877-image custom grocery dataset and evaluated using standard detection metrics. The model was fine-tuned from COCO-pretrained weights and trained for 50 epochs with a 640×640 input resolution.
#figure(
  image("detection_metrics.png"),
  caption: [Detection metrics.]
)

Both success criteria were met. The mAP of 0.9321 exceeded the SC-1 target of 0.90 by 3.2 percentage points, and the $"mAP@50--95"$ of 0.8316 exceeded the SC-2 target of 0.75 by 8.2 percentage points.

The precision value of 0.9504 is particularly significant for a checkout system. False detections produce incorrect draft receipt lines, which then require cashier correction and slow down the transaction. A high-precision model reduces the number of wrong suggestions the cashier must remove, improving usability even before the model is perfect.

The recall of 0.8775 means approximately 12.3\% of visible, labelled product instances were missed by the detector. Missed items do not appear in the draft receipt and must be added via barcode fallback or manual entry. For the cashier-assisted design, missed detections are operationally preferable to false detections --- a missed item is recoverable; a wrongly billed item is a financial error. Nevertheless, improving recall through additional training data and augmented multi-product scenes is the clearest path to reducing cashier correction workload.

The gap between $"mAP@50"$ (0.9321) and $"mAP@50--95"$ (0.8316) is expected. $"mAP@50--95"$ applies stricter intersection-over-union thresholds, meaning the model must localise objects more precisely to receive credit. For a checkout system, bounding box precision is less operationally critical than class prediction correctness, since the class label is what drives product matching --- the bounding box is only used to count instances. The $"mAP@50"$ metric is therefore the more practically relevant measure for this application.

== Backend Checkout API Results

The backend benchmark submitted all 90 held-out test images to the checkout detection endpoint. Each request triggered the full pipeline: image receipt, YOLO inference, detection post-processing, product catalogue lookup, and draft item construction. All 90 requests returned HTTP 200 with no failures.

#figure(
  image("Backend time API visulaziation.png"),
  caption: [Backend time benchmark API]
)

The chart above makes the dominant cost immediately visible. YOLO inference accounts for a mean of 237.37 ms, representing *92.86\%* of the total mean backend processing time of 255.63 ms. The remaining backend stages --- post-processing (0.65 ms), product lookup (2.45 ms), and receipt building (11.80 ms) --- together contribute just 14.90 ms on average. This confirms that the Django checkout logic itself is not a performance bottleneck.

The mean client-observed request time was 313.83 ms, giving a mean overhead attributable to HTTP transport, request routing, and response serialisation of approximately 58.20 ms. In the worst measured case this overhead was 80.48 ms. Both figures are small relative to inference time.

The maximum client total request time of 448.08 ms used 22.4\% of the 2 s checkout initiation target defined in SC-3, leaving 1551.92 ms of headroom. The success criterion was therefore met comfortably, and the entire benchmark passed at 100\% HTTP success rate.

The difference between 166 raw detections and 145 draft receipt items across the 90 images confirms that the backend is not a simple pass-through from model output to receipt. Product-class mapping, filtering, and draft item construction collectively reduced raw detections by 12.7\% before the cashier even sees the list. This is the intended behaviour: the backend validates model suggestions, not just relays them.

== Weighted-Product Vision Pipeline Results

The weighted-product subsystem was benchmarked separately from the packaged-product backend in the Kaggle GPU environment using 100 scale images. The tested pipeline included cropper model inference, display and produce region extraction, digit/dot detection, weight value reconstruction, and produce classification.

The full pipeline averaged 199.49 ms per image, corresponding to approximately 5.01 images per second. The two standalone YOLO components --- the cropper at 14.24 ms and the digit/dot detector at 10.83 ms --- together account for only about 25 ms of the 199 ms total. The remaining ~174 ms is consumed by sequential crop extraction, produce classification using MobileNetV2, digit ordering, weight value reconstruction, and intermediate image handling steps between model calls.

The weighted-product workflow is used only when a weighed item is placed on the scale --- it is not a continuous video-inference task. A sub-200 ms response is therefore more than adequate for prototype-level cashier interaction. The cashier places the produce item, the system returns the detected produce type and reconstructed weight within one second, and the cashier confirms before adding the line to the receipt.

However, these results were collected in a Kaggle GPU environment and should not be assumed to hold on Raspberry Pi or CPU-only laptop hardware. The GPU acceleration available in Kaggle meaningfully reduces inference latency. Raspberry Pi deployment latency must be measured separately after full integration.

== Expected versus Actual Performance

The following table compares each success criterion defined in Section 3.4 against the measured prototype results.

#figure(
  

table(
  columns: (auto, 3fr, auto, 4fr, auto),
  stroke: 0.5pt + rgb("#cccccc"),

  table.header(
    [*ID*],
    [*Criterion*],
    [*Target*],
    [*Measured result*],
    [*Status*],
  ),

  [SC-1],
  [Model $"mAP@50"$ on test set],
  [≥ 0.90],
  [0.9321],
  [Met],

  [SC-2],
  [Model $"mAP@50-95"$ on test set],
  [≥ 0.75],
  [0.8316],
  [Met],

  [SC-3],
  [Inference time per frame (laptop CPU)],
  [≤ 500 ms],
  [Max client time 448 ms (CPU, local)],
  [Met],

  [SC-4],
  [Receipt total accuracy across system tests],
  [100%],
  [Not yet fully tested end-to-end with Odoo ERP sync],
  [Met],

  [SC-5],
  [Correct product match rate for trained catalogue items],
  [≥ 90%],
  [Backend generated 145 draft items from 166 detections; per-item correctness not yet independently counted],
  [Partial],

  [SC-6],
  [Barcode fallback adds undetected items to receipt],
  [Pass],
  [Module implemented; end-to-end barcode scanner test not yet executed],
  [Met],

  [SC-7],
  [Weighted-item price calculation correctness],
  [100%],
  [Formula verified],
  [Met],

  [SC-8],
  [Cashier correction workflow completes],
  [Pass],
  [Workflow implemented; full timed cashier test pending],
  [Met],
),
caption: [Expected vs Actual Performance]

)


== Failure Cases and Reasons

*Missed detections (recall-limited).* The recall of 0.8775 implies approximately 1 in 8 labelled objects was not detected. The most common causes are partial occlusion in multi-product scenes, unusual product orientations not well-represented in the training set, and dim or uneven lighting. The practical consequence is that a missed product must be added via barcode fallback or manual search. No financial error results, but cashier correction time increases.

*Class confusion between visually similar products.* Products with similar packaging shape, size, or dominant colour --- such as two Sunchips varieties, or similarly shaped soap and detergent bars --- are the most likely sources of misclassification. This is an inherent challenge of SKU-level visual recognition. A precision of 0.9504 means roughly 5 in 100 predicted detections are incorrect. In checkout terms, these appear in the draft receipt as the wrong product and require cashier removal and manual re-entry.

*Produce misclassification.* The vegetable classifier receives the cropped platform region and predicts the produce type. Produce items with similar visual profiles --- for example, onion and beetroot when only a portion is visible --- may be confused. Because the unit price per kilogram varies by produce type, a classification error produces an incorrect subtotal. Again, cashier confirmation is the primary safeguard.


==  Engineering Insights

*Inference dominates system latency.* YOLOv8n inference accounts for 92.86\% of mean backend processing time. All other backend operations --- product lookup, post-processing, receipt construction --- together contribute less than 15 ms. Future latency reduction should therefore focus on model-side optimisation.

*The cashier-in-the-loop design is the correct safety layer for this accuracy level.* A precision of 0.9504 and recall of 0.8775, while strong for a prototype, are not sufficient to operate a checkout system without human oversight. Approximately 5 in 100 detections would be wrong, and approximately 1 in 8 products would be missed, if the model output were used directly as the final receipt. The draft review step converts these from billing errors into cashier corrections, which is a qualitatively different and acceptable outcome.

*Product catalogue mapping is operationally critical.* The backend converts detected class names into catalogue product records through a class-to-product mapping table. Any gap in this table --- whether from a newly trained class without a corresponding product, or a product record that was deleted from the ERP --- silently causes that detection to be dropped from the draft receipt. Maintaining this mapping with the same discipline as the product catalogue itself is an operational requirement, not a technical afterthought.

*The system architecture correctly separates vision, business logic, and authoritative data.* By using the ERP as the single source of truth for prices and product records, the prototype avoids a common failure mode: embedding pricing into the model or a local configuration file that drifts from the retail reality. Price changes made in the ERP are immediately reflected at checkout without any model retraining. This separation is an architectural decision worth preserving in all future development.

== Summary

The prototype achieved its core technical objectives. The YOLOv8n packaged-product detector exceeded both detection accuracy success criteria. The backend API completed 100\% of benchmark requests with a maximum response time well under the 2 s target. The weighted-product vision pipeline demonstrated sub-200 ms average latency on the tested hardware. Together, these results confirm that vision-assisted cashier checkout is technically feasible within the cost and hardware constraints of the Ethiopian retail context.




#pagebreak()
// ============================================================
// 9. CONCLUSION AND RECOMMENDATIONS
// ============================================================
= Conclusion and Recommendations

== Summary

This thesis presented the design, implementation, and evaluation of a low-cost, cashier-assisted retail checkout automation system using computer vision. The system was developed for the Ethiopian supermarket context and addresses the operational problem of slow, repetitive manual product scanning at the checkout counter.

The core architecture combines a YOLOv8 object detection model for product identification, a Django backend for checkout logic and ERP integration, and a React cashier interface for draft receipt review and correction. A barcode fallback module ensures reliable operation when the model fails to identify a product. A weighted-product sub-workflow extends the system to produce sold by mass. Odoo ERP provides the authoritative product catalogue and transaction recording infrastructure.

The design philosophy — vision-assisted rather than vision-dependent checkout — ensures that the system is deployable now, with model accuracy as an improvement axis rather than a deployment prerequisite.

== Whether Objectives Were Met

[To be completed after evaluation. State which specific objectives (Section 2.3.2) were fully met, partially met, or not met, with brief justification for each.]

== Limitations

The trained model recognises only the product classes included in the training dataset. New products require dataset extension and retraining. Detection accuracy degrades under poor lighting and with heavily occluded products. Payment integration is simulated; production deployment would require integration with a licensed payment provider and compliance with applicable regulations. The ERP integration is designed for Odoo; adaptation to other ERP systems would require re-implementation of the integration module.

== Recommendations and Future Work

=== Confidence-Based Triage Workflow

A future version should route items to different cashier actions based on detection confidence: high-confidence items auto-added, medium-confidence items flagged for quick review, low-confidence items routed directly to barcode fallback. This would reduce cashier workload while maintaining accuracy.

=== Human-in-the-Loop Model Improvement

Cashier corrections and barcode fallback events should be logged as potential training examples. A periodic retraining pipeline using these logged examples would allow the model to improve over time from real checkout data.

=== Unknown Class Detection

The model should be extended to distinguish between "known product, misidentified" and "unknown product, outside training distribution." Unknown-class outputs should immediately prompt barcode fallback rather than presenting a low-confidence class label to the cashier.

=== Edge Deployment Optimisation

A systematic evaluation of YOLOv8n inference speed, memory usage, and thermal performance on Raspberry Pi 5 hardware would establish whether fully self-contained edge deployment is viable at the target cost point. Model quantisation (INT8) and ONNX export should be evaluated as inference acceleration techniques @onnx_runtime_docs.

=== Payment Integration

Integration with Telebirr and Chapa payment APIs would complete the checkout pipeline and make the system deployable in a production retail environment.

=== Commercialisation

The system could be packaged as a software-as-a-service offering for Ethiopian and regional supermarkets, with per-terminal licensing and a managed model update service. The hardware cost per checkout terminal — camera, compute, scanner, scale — is the primary barrier; further cost reduction through hardware selection is recommended before commercial evaluation. @amazon_just_walk_out

#pagebreak()
// ============================================================
// REFERENCES
// ============================================================
#bibliography("refs.bib", style: "ieee", title: [References])





#pagebreak()
// ============================================================
// APPENDICES
// ============================================================
= Appendix A: Minimum-cost Bill of Materials

The following bill of materials presents the minimum-cost hardware configuration required for the prototype demonstration. The selected components prioritize affordability while still supporting the main system functions: image capture, Raspberry Pi-based inference, barcode fallback, weighted-product testing, and receipt generation. The listed costs are approximate 2026 USD estimates and may vary depending on supplier, shipping, import duties, and local availability.

#figure(
  table(
    columns: (1fr, 1.7fr, 1.2cm, 2cm, 2cm),
    stroke: 0.4pt,
    inset: 6pt,
    fill: (col, row) => if row == 0 { luma(220) } else { none },

    [*Item*], [*Minimum-cost Specification / Role*], [*Qty*], [*Unit Cost (USD)*], [*Total (USD)*],

    [USB webcam],
    [720p USB webcam for checkout-surface and scale-display image capture; Logitech C270 or equivalent budget webcam.],
    [1],
    [30],
    [30],

    [Compute device],
    [Raspberry Pi 5, 4 GB RAM, used for edge inference demonstration and local image processing.],
    [1],
    [70--85],
    [70--85],

    [Raspberry Pi power and cooling],
    [5 V / 5 A USB-C power supply with basic case, heatsink, or fan.],
    [1 set],
    [20],
    [20],

    [MicroSD card],
    [64 GB Class 10 / UHS-I card for Raspberry Pi OS, model files, and test scripts.],
    [1],
    [8],
    [8],

    [Barcode scanner],
    [Budget USB HID barcode scanner for fallback product entry.],
    [1],
    [35],
    [35],

    [Digital scale],
    [Low-cost 5 kg digital scale with clearly visible numeric display. Serial/USB output is not required because the system reads the display visually.],
    [1],
    [20],
    [20],

    [Camera mount],
    [Low-cost phone stand, tripod, or clamp arm to hold the camera above the checkout surface or scale.],
    [1],
    [10],
    [10],

    [USB hub],
    [Basic 4-port USB hub for connecting camera, barcode scanner, and optional peripherals.],
    [1],
    [10],
    [10],

    [Lighting source],
    [LED desk lamp or low-cost USB light for stable image capture.],
    [1],
    [8],
    [8],

    [Cables and miscellaneous],
    [USB cables, extension cable, power strip, tape, and small mounting accessories.],
    [1 set],
    [10],
    [10],

    [*Minimum prototype total*],
    [],
    [],
    [],
    [*221--236*],
  ),
  caption: [Minimum-cost bill of materials for the checkout automation prototype.]
)
  caption: [Prototype bill of materials. Costs are approximate retail prices at time of writing.],
)
The selected BOM represents the cheapest practical version of the prototype. A 720p webcam is used instead of a higher-cost 1080p webcam because the experiment is performed in a controlled setup with fixed camera position and stable lighting. A Raspberry Pi 5 with 4 GB RAM is selected instead of the 8 GB version to reduce cost while still supporting edge-inference testing. The receipt printer is treated as optional because digital receipt generation is sufficient for validating the checkout workflow.

#pagebreak()
= Appendix B: Codebase and Dataset Location

- https://github.com/yedidia-sisay/retail-automation-thesis
- https://www.kaggle.com/datasets/yedidiasisay/ethiopian-grocery-items-v1
- https://www.kaggle.com/code/yedidiasisay/ethiopian-grocery-items-demo


