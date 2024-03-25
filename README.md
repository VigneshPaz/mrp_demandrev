# mrp_demandrev
linear programming model for optimizing the order quantities and inventory in the supply chain for revised production schedule

README File

How to use the code:

Step 1: Download the below files (python code and input data files) from the repository to your working directory:

DemandRev.py - Python code available in main branch
demandi.csv - Revised demand input file available in Illustrative_Example folder or the LargeScale_Instance folder.
bomi.csv - Bill of material input file available in Illustrative_Example folder or the LargeScale_Instance folder.
incominginventoryi.csv - Incoming inventory of parts input file available in Illustrative_Example folder or the LargeScale_Instance folder.
onhandi.csv – On-hand inventory of parts input file available in Illustrative_Example folder or the LargeScale_Instance folder.
penaltyi.csv - Penalty for premium and regular mode input file available in Illustrative_Example folder or the LargeScale_Instance folder.
transittimei.csv - Transit time of parts input file available in Illustrative_Example folder or the LargeScale_Instance folder.
Step 2: Update your input files with the data as outlined below.

demandi.csv - This file should contain the revised demand at vehicle model level (Vehicle_model) for all the periods (time_period). Any period with no volume should be marked as zero.
bomi.csv - The file should contain the part list (part_number) against all the vehicle model (Vehicle_model) for each period (time_period) and their usage quantity. All parts should be available for all vehicle models and if some parts are not used in the vehicle model it should be marked with zero quantity.
incominginventoryi.csv - The file should contain the quantity of parts incoming parts at each period (time_period). All parts in the bill of material should be listed and if some parts have no incoming inventory, it should be filled with zero quantity.
onhandi.csv - This file should contain the on-hand inventory (On_hand), supplier capacity (Supplier_capacity) and supplier name or code (Supplier) of the parts. Supplier field is used for reporting purpose and not used in the model. All parts in the bill of material should be listed and if some parts have no on hand it should be filled with zero quantity.
penaltyi.csv - This file should contain the penalty (Penalty) for the regular mode (R) and premium mode (P) shipment.
transittimei.csv - This file should contain the transit time (Transit_time) of parts for each mode of shipment (regular and premium mode). Source (Source, part rating (Part_Rating) and analyst (Analyst) fields are for reference and not used in the model. All parts in the bill of material should be listed with the transit time for each mode of shipment. If the regular and premium mode has the same transit time, input the same value for both the modes.
Caution:

Column names should not be modified.
Addition of columns or deletion of existing columns should not be done.
Step 3: Run the python code DemandRev.py. This will create two output files Results_ArrOrderQuan.csv and Results_Other.csv in your working directory.

How to read the output:

Results_ArrOrderQuan.csv - This file provides the user with the parts (part_number) order quantity (OrderQty), arrival quantity (ArrivalQty) for premium and regular mode (mode) at each period (time_period). Results_Other.csv - This file provides the user with inventory (Inventory), capacity shortfall (PositiveSlack), capacity balance (NegativeSlack) and demand shortfall (DemandSlack) for all the parts (part_number) at each period (time_period). Note:

DemandSlack field will have only positive values. Any postive value represents a demand shortfall in that period. A zero value represents no shortfall.
PositiveSlack field will have only positive values. Any postive value represents capacity shortfall in that period. A zero value represents no shortfall, and the available capacity is reported in NegativeSlack field.
