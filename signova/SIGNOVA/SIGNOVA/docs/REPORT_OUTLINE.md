# Project report outline - SIGNOVA

1. **Title page, certificate, acknowledgement, abstract, keywords**
2. **Introduction** - communication barriers, motivation, problem statement, objectives, scope
   (app-defined gesture vocabulary, *not* full sign-language translation)
3. **Literature survey** - sign-language recognition approaches (sensor gloves, vision-based, CNN/LSTM,
   landmark-based), MediaPipe Hands, existing tools, gaps
4. **System analysis** - existing vs proposed system, functional and non-functional requirements,
   feasibility, hardware and software requirements
5. **System design** - architecture diagram, data-flow diagrams, module design, database schema
   (`translations`: id, text, word_count, created_at), UI design and theme
6. **Methodology** - capture, 21-landmark tracking, finger-extension features, rule-based pose
   classification, trajectory analysis for motions, hold-to-confirm, text and speech output
7. **Implementation** - technology stack, key modules and algorithms, screenshots
8. **Testing and results** - unit tests with synthetic landmarks, manual test table, per-gesture trial
   results from real users, failure cases, limitations of the evaluation
9. **Privacy, ethics and reliability** - local processing, no video storage, bias/lighting/skin-tone and
   hand-size considerations, avoiding overclaiming
10. **Limitations and future scope** - larger vocabulary, trained classifier, sequences, two hands,
    facial cues, mobile deployment, user study with the Deaf community
11. **Conclusion**
12. **References** and **Appendices** (source listing, user manual, test cases)
