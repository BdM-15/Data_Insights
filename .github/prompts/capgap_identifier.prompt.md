#### Capability Assessment Prompt

#### Purpose
This prompt is designed to assist users in identifying capabilities from past contract and subcontract awards, analyzing subcontractor prime awards, and assessing potential capability gaps in relation to future opportunities.

#### Prompt
```
You are tasked with conducting a capability assessment based on contract and subcontract data foudn in the capture_insights postgreSQL database on a specific company or list of companies. Please address the following:
1. What capabilities can be identified from past contract awards and subcontract awards to subcontractors?  This will be done for our company and for the competitors identified by the user.
2. For the subcontract awards identified in 1. above, do another round of capabilities searches to see what that subcontractors with prime awards specializes that provide additional insights into their capabilities?
3. Develop a company profile with all identified competitors and summarize the contractors capability information, such as name, UEI, parent company and include key words and phrases that can be used for semantic searches and serve as a knowledge base for LLM interaction.
4. How do these identified capabilities align with future opportunity data?  This opportunity may be specifically identified by the user.
5. Are there any potential capability gaps that may require teaming partners to address?
6. What recommendations can be made to strengthen the our companies capability assessment and address identified gaps compared to our competitors?

Ensure your response is thorough, well-organized, and actionable.
```

#### Why This is Useful
- **Comprehensive Analysis**: Facilitates a detailed review of past and present capabilities.
- **Future Alignment**: Helps identify gaps in relation to upcoming opportunities.
- **Supports Teaming Decisions**: Provides insights for forming strategic partnerships.
- **Actionable Insights**: Encourages recommendations to enhance capability alignment.

This prompt can be integrated into workflows for business development, proposal preparation, and strategic planning to ensure a robust capability assessment process.