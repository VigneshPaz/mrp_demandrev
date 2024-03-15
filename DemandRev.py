import logging
import pyomo
import pandas
import pyomo.opt
import pyomo.environ as pe
import sys

class DemandRev:
    
    def __init__(self, bomfile, demandfile, invenfile, onhandfile, transitfile, penaltyfile, capacity_penalty, demand_penalty):
        """Read in the csv data."""
        # Read in the bom file
        self.bom_data_raw = pandas.read_csv(bomfile)
        self.bom_data = pandas.melt(self.bom_data_raw,id_vars=['Vehicle_model','Part_number'])
        #self.bom_data['variable'] = self.bom_data['variable'].map(lambda x: x.lstrip('tT'))
        self.bom_data['variable'] = self.bom_data['variable'].astype(int)
        self.bom_data = self.bom_data.rename(columns={"variable": "TimePeriod", "value": "bom_qty"})
        self.bom_data['bom_qty'] = self.bom_data['bom_qty'].fillna(0)
        self.bom_data.set_index(['Vehicle_model','Part_number','TimePeriod'], inplace=True)
        self.bom_data.sort_index(inplace=True)
        
        # Read in the demand file
        self.demand_data_raw = pandas.read_csv(demandfile)
        self.demand_data = pandas.melt(self.demand_data_raw,id_vars='Vehicle_model')
        #self.demand_data['variable'] = self.demand_data['variable'].map(lambda x: x.lstrip('tT'))
        self.demand_data['variable'] = self.demand_data['variable'].astype(int)
        self.demand_data = self.demand_data.rename(columns={"variable": "TimePeriod", "value": "demand_qty"})
        self.demand_data['demand_qty'] = self.demand_data['demand_qty'].fillna(0)
        self.demand_data.set_index(['Vehicle_model','TimePeriod'], inplace=True)
        self.demand_data.sort_index(inplace=True)    
        
        # Read in the incoming inventory file
        self.inventory_data_raw = pandas.read_csv(invenfile)
        self.inventory_data = pandas.melt(self.inventory_data_raw,id_vars='Part_number')
        #self.inventory_data['variable'] = self.inventory_data['variable'].map(lambda x: x.lstrip('tT'))
        self.inventory_data['variable'] = self.inventory_data['variable'].astype(int)
        self.inventory_data = self.inventory_data.rename(columns={"variable": "TimePeriod", "value": "inventory_qty"})
        self.inventory_data['inventory_qty'] = self.inventory_data['inventory_qty'].fillna(0)
        self.inventory_data.set_index(['Part_number','TimePeriod'], inplace=True)
        self.inventory_data.sort_index(inplace=True)   
        
         # Read in the incoming onhand file
        self.onhand_data = pandas.read_csv(onhandfile)
        self.onhand_data['On_hand'] = self.onhand_data['On_hand'].fillna(0)
        self.onhand_data['Supplier_capacity'] = self.onhand_data['Supplier_capacity'].fillna(0)
        self.onhand_data.set_index(['Part_number'], inplace=True)
        self.onhand_data.sort_index(inplace=True)    
        
        # Read in the incoming transit time file
        self.transit_data = pandas.read_csv(transitfile)
        self.transit_data['Transit_time'] = self.transit_data['Transit_time'].fillna(0)
        self.transit_data.set_index(['Part_number','Mode'], inplace=True)
        self.transit_data.sort_index(inplace=True)   
        
        # Read in the penalty file
        self.penalty_data = pandas.read_csv(penaltyfile)
        self.penalty_data['Penalty'] = self.penalty_data['Penalty'].fillna(0)
        self.penalty_data.set_index(['Mode'], inplace=True)
        self.penalty_data.sort_index(inplace=True)   
        
  
        self.bom_set = self.bom_data.index.unique()
        self.demand_set = self.demand_data.index.unique()
        self.inventory_set = self.inventory_data.index.unique()
        self.onhand_set = self.onhand_data.index.unique()
        self.transit_set = self.transit_data.index.unique()
        self.penalty_set = self.penalty_data.index.unique()
        self.vehicle_set = self.demand_data.index.get_level_values(0).unique()
        
        self.capacity_theta = capacity_penalty
        self.demand_theta = demand_penalty
             
        self.createModel()


    def createModel(self):
        """Create the pyomo model given the csv data."""
        self.m = pe.ConcreteModel()
        
        # Create sets
        self.m.demand_set = pe.Set( initialize=self.demand_set, dimen=2)
        self.m.transit_set = pe.Set( initialize=self.transit_set)
        self.m.onhand_set = pe.Set( initialize=self.onhand_set)
        self.m.inventory_set = pe.Set( initialize=self.inventory_set, dimen=2)
        self.m.bom_set = pe.Set( initialize=self.bom_set, dimen=3)
        self.m.penalty_set = pe.Set( initialize=self.penalty_set)      
        self.m.part_time_mode_set = pe.Set(initialize= ((j,t,m) for (j,t) in self.inventory_set for m in self.penalty_set), dimen=3)

        #param s := Zoo;
        
        # Create variables
        self.m.INVENTORY = pe.Var(self.m.inventory_set, domain=pe.NonNegativeReals)  
        self.m.NET_REQ = pe.Var(self.m.inventory_set, domain=pe.Any)  
        self.m.ARR_QTY = pe.Var(self.m.part_time_mode_set, domain=pe.NonNegativeReals)
        self.m.ORDER_QTY = pe.Var(self.m.part_time_mode_set, domain=pe.NonNegativeReals)
        #self.m.CAP_SLACK = pe.Var(self.m.inventory_set, domain=pe.NonNegativeReals) 
        self.m.POS_CAP_SLACK = pe.Var(self.m.inventory_set, domain=pe.NonNegativeReals)     
        self.m.NEG_CAP_SLACK = pe.Var(self.m.inventory_set, domain=pe.NonNegativeReals)  
        self.m.DEM_SLACK = pe.Var(self.m.inventory_set, domain=pe.NonNegativeReals)

        # Create objective
        def obj_rule(m):
            return sum( ((self.m.POS_CAP_SLACK[j,t] * self.capacity_theta) + (self.m.DEM_SLACK[j,t] * self.demand_theta)) for (j,t) in self.inventory_set) + sum(self.m.ORDER_QTY[j,t,m] * self.penalty_data.loc[m,'Penalty'] for (j,t,m) in self.m.part_time_mode_set)
            #return sum( ((self.m.CAP_SLACK[j,t] * self.capacity_theta) + (self.m.DEM_SLACK[j,t] * self.demand_theta)) for (j,t) in self.inventory_set) + sum(self.m.ORDER_QTY[j,t,m] * self.penalty_data.loc[m,'Penalty'] for (j,t,m) in self.m.part_time_mode_set)
        self.m.OBJ = pe.Objective(rule=obj_rule, sense=pe.minimize)

        # Create constraints
        def inventory_calc_rule(m, j, t):
          return self.m.INVENTORY[j,t] >= 0
        self.m.inventoryCalc = pe.Constraint(self.m.inventory_set, rule=inventory_calc_rule, doc='Inventory is greater or equal to than 0')

        def inventory_calc1_rule(m, j, t):
            if t == 1: 
                return self.m.INVENTORY[j,t] >= self.onhand_data.loc[j,'On_hand'] + self.inventory_data.loc[(j,t),'inventory_qty'] + sum(self.m.ARR_QTY[j,t,m1] for m1 in self.penalty_set) - sum(self.demand_data.loc[(i,t),'demand_qty'] * self.bom_data.loc[(i,j,t),'bom_qty'] for i in self.vehicle_set)
            else:
                return self.m.INVENTORY[j,t] >= self.m.INVENTORY[j,t-1] + self.inventory_data.loc[(j,t),'inventory_qty'] + sum(self.m.ARR_QTY[j,t,m1] for m1 in self.penalty_set) - sum(self.demand_data.loc[(i,t),'demand_qty'] * self.bom_data.loc[(i,j,t),'bom_qty'] for i in self.vehicle_set)
        self.m.inventoryCalc1 = pe.Constraint(self.m.inventory_set, rule=inventory_calc1_rule, doc='Inventory computation')

        def net_req_calc1_rule(m, j, t):
            if t == 1: 
                return self.m.NET_REQ[j,t] == sum(self.demand_data.loc[(i,t),'demand_qty'] * self.bom_data.loc[(i,j,t),'bom_qty'] for i in self.vehicle_set)  - self.onhand_data.loc[j,'On_hand'] - self.inventory_data.loc[(j,t),'inventory_qty']
            else:
                return self.m.NET_REQ[j,t] == sum(self.demand_data.loc[(i,t),'demand_qty'] * self.bom_data.loc[(i,j,t),'bom_qty'] for i in self.vehicle_set) - self.m.INVENTORY[j,t-1] - self.inventory_data.loc[(j,t),'inventory_qty']
        self.m.netreqCalc = pe.Constraint(self.m.inventory_set, rule=net_req_calc1_rule, doc='Net requirement computation')

        def parts_order_calc_rule(m, j, t, d):
            if t - self.transit_data.loc[(j,d),'Transit_time'] > 0:
                return self.m.ARR_QTY[j,t,d] == self.m.ORDER_QTY[j,t - self.transit_data.loc[(j,d),'Transit_time'],d]
            else:
                return self.m.ARR_QTY[j,t,d] == 0 
        self.m.partOrderCalc = pe.Constraint(self.m.part_time_mode_set, rule=parts_order_calc_rule, doc='Arrival quantity computation')
        
        def demand_calc_rule(m, j, t):
            if t == 1: 
                return self.onhand_data.loc[j,'On_hand'] + self.inventory_data.loc[(j,t),'inventory_qty'] + sum(self.m.ARR_QTY[j,t,m1] for m1 in self.penalty_set) - self.m.INVENTORY[j,t] == sum(self.demand_data.loc[(i,t),'demand_qty'] * self.bom_data.loc[(i,j,t),'bom_qty'] for i in self.vehicle_set) - self.m.DEM_SLACK[j,t] 
            else:
                return self.m.INVENTORY[j,t-1] + self.inventory_data.loc[(j,t),'inventory_qty'] + sum(self.m.ARR_QTY[j,t,m1] for m1 in self.penalty_set) - self.m.INVENTORY[j,t] == sum(self.demand_data.loc[(i,t),'demand_qty'] * self.bom_data.loc[(i,j,t),'bom_qty'] for i in self.vehicle_set) - self.m.DEM_SLACK[j,t] 
        self.m.demandCalc = pe.Constraint(self.m.inventory_set, rule=demand_calc_rule, doc='Demand constraint')        

        def capacity_calc_rule(m, j, t):
            return sum(self.m.ORDER_QTY[j,t,m1] for m1 in self.penalty_set) == self.onhand_data.loc[j,'Supplier_capacity'] +  self.m.POS_CAP_SLACK[j,t] - self.m.NEG_CAP_SLACK[j,t]
            #return sum(self.m.ORDER_QTY[j,t,m] for m in self.penalty_set) == self.onhand_data.loc[j,'Supplier_capacity'] +  self.m.CAP_SLACK[j,t]
        self.m.capacityCalc = pe.Constraint(self.m.inventory_set, rule=capacity_calc_rule, doc='Capacity constraint')    


    def solve(self):
        """Solve the model."""
        solver = pyomo.opt.SolverFactory('glpk')
        results = solver.solve(self.m, tee=True, logfile="logfile.log", keepfiles=False, options_string="tmlim=600 mipgap=0.0001")
        
        x = str(self.m)
        x = str(self.m.pprint()) 

        
        if (results.solver.status != pyomo.opt.SolverStatus.ok):
            logging.warning('Check solver not ok?')
        if (results.solver.termination_condition != pyomo.opt.TerminationCondition.optimal):  
            logging.warning('Check solver optimality?')

        # Reference: https://groups.google.com/g/pyomo-forum/c/nbynW4EPTMk
        with open("Results_ArrOrderQuan.csv", "w") as f:
            f.write("part_number,time_period,mode,OrderQty,ArrivalQty\n")
            for (j,t,m) in self.m.part_time_mode_set:
                f.write("%s,%s,%s,%s,%s\n" % (j, t, m, self.m.ORDER_QTY[j,t,m].value,self.m.ARR_QTY[j,t,m].value))
            
        with open("Results_Other.csv", "w") as f:
            f.write("part_number,time_period,Inventory,PositiveSlack,NegativeSlack,DemandSlack\n")
            #f.write("part_number,time_period,Inventory,Slack,DemandSlack\n")
            for (j,t) in self.m.inventory_set:
                f.write("%s,%s,%s,%s,%s,%s\n" % (j, t, self.m.INVENTORY[j,t].value, self.m.POS_CAP_SLACK[j,t].value, self.m.NEG_CAP_SLACK[j,t].value, self.m.DEM_SLACK[j,t].value))
                #f.write("%s,%s,%s,%s,%s\n" % (j, t, self.m.INVENTORY[j,t].value, self.m.CAP_SLACK[j,t].value, self.m.DEM_SLACK[j,t].value))


if __name__ == '__main__':
    sp = DemandRev('bomi.csv', 'demandi.csv', 'incominginventoryi.csv', 'onhandi.csv', 'transittimei.csv', 'penaltyi.csv', 100, 200)
    sp.solve()
    print('\n\n---------------------------')
    print('Cost: ', sp.m.OBJ())


    # Print statements for debug 
    # print(sp.capacity_theta)
    # print(sp.demand_theta)
    # print(sp.bom_data)
    # print(sp.demand_data)
    # print(sp.inventory_data)
    # print(sp.onhand_data)
    # print(sp.transit_data)
    # print(sp.penalty_data)
    # print(sp.penalty_set)
    # print(type(sp.transit_data['Transit_time']))