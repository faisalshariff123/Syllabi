# Syllabus to Calendar

Takes a syllabus PDF and spits out an .ics file with every deadline and exam in it, ready to import into your calendar.

This isn't just an LLM wrapper. The actual point of the project is the eval harness that checks if the extraction is even accurate, plus a manual confirm step before anything gets exported because no extractor is perfect and I'm not pretending otherwise.

## How it flows

```
PDF -> pull text out with pypdf -> LLM pulls out dates as JSON (extractor.py)
                                          |
                                          v
                    eval harness scores it against ground truth (eval/run_eval.py)
                                          |
                        you review/edit the deadlines in the frontend
                                          |
                                          v
                              export to .ics (ics_export.py)
```


1. **Term start date gets fed to the model** so items like "Week 3 Friday" turns into an actual date.
2. **Extract and export are two separate steps.** You get to check and fix things before it exports.


