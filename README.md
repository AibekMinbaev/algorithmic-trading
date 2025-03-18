

Repository contains the algorithmic trading strategy that I built as final project at "Business Lab for Financial Engineering (FIA432)" course at UNIST in Spring 2024.  


## Moving Average Convergence Divergence (MACD) 

MACD is an indicator that helps traders to identify trends. 

It consists of 4 indicator lines: 
- MACD line - 12 day exponetial moving average
- Signal line - 26 day exponential moving average
- Histogram
- Zero line - center of the indicator 
- 200 days of Moving Average 


Using these indicators we find buy or sell indicators. 

- Buy signal 
When MACD line crosses above the Signal line ONLY when it is below the Zero line 

- Sell signal 
When MACD line crosses below the Signal line ONLY when it is above the Zero line 


Sometimes the MACD gives false signals to buy even if there is not upward trend. 
To solve this problem we can use 200 days Moving Average. 


Backetesting code for MACD: https://colab.research.google.com/drive/1GDLaqoEQAXSHCAx2i0_0LCJLUgEaNI8i?usp=sharing