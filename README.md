``` mermaid
graph LR;
%% Query 1
%% Define sources
    SBP@{shape: in-out, label: "Systolic Blood Pressure"}
    HR@{shape: in-out, label: "Heart Rate"}
    SpO2@{shape: in-out, label: "SpO2"}
    IR@{shape: in-out, label: "IR Video"}
    YUYV@{shape: in-out, label: "YUYV Video"}
    pRGB@{shape: proc, label: "YUYV 2 RGB"}
    RGB@{shape: event, label: "RGB Video"}
    Audio@{shape: in-out, label: "Audio"}
    LungXRay@{shape: in-out, label: "Lung X-Ray"}

    YUYV -->pRGB --> RGB

%% Query ARDS
    subgraph ARDS Query
        
        dTachy@{shape: diamond, label: "HR > 100"}
        dHypox@{shape: diamond, label: "SpO2 <= 97"}
        dCrackle@{shape: proc, label: "Crackle Classifier"}
        pLungBright@{shape: proc, label: "Avg Brightness"}
        dLungBright@{shape: diamond, label: "Avg Bright > XXX"}
        jARDS@{shape: join, label: "Join ARDS Symptoms"}
        dTachy --> jARDS
        dHypox --> jARDS
        dCrackle --> jARDS
        jARDS --> AlertSuggestXRay@{shape: in-out, label: "Smart Alert Suggest Investigate ARDS"}
        pLungBright --> dLungBright --> jARDS
      
    end

    HR --> dTachy
    SpO2 --> dHypox
    Audio --> dCrackle
    LungXRay --> pLungBright 

%% Query Shock
    subgraph Shock Query
        jSI@{shape: join, label: "Join on Time Window"} 
        jSI --> procSI@{shape: proc, label: "HR / SBP = Shock Index"}
        procSI --> dSI@{shape: diamond, label: "Shock Index > 1" }
        AlertShock@{shape: in-out, label: "Smart Alert notify Shock Risk 1"}
        dSI --> AlertShock

        subgraph IR - RGB Alignment
            jKP@{shape: join, label: "Join KP"}
            kpIR@{shape: proc, label: "Key Points IR"} --> jKP
            kpRGB@{shape: proc, label: "Key Points RGB"} --> jKP
            mKP@{shape: proc, label: "Match Points Calculate XY IR Offset"}
            jKP --> mKP
            jObj@{shape: join, label: "Join Obj to Offset"}
            mObj@{shape: proc, label: "Align RGB Obj to IR"}
            mKP --> jObj --> mObj
        end

        objDect@{shape: proc, label: "Object Detection"}
        objDect --> obj@{ shape: event, label: "Object Bounding Box"}
        obj --> jObj
        dShockTemp@{shape: diamond, label: "Avg Obj Temp < 28"}
        mObj --> dShockTemp --> AlertShock

    end

    %% Connections outside subgraphs
    RGB --> objDect
    SBP --> jSI
    HR --> jSI
    IR --> kpIR
    RGB --> kpRGB
```
