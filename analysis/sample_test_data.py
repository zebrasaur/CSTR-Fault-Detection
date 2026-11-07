#test data


#TRUTH
run_id,time,fault_kind,severity,onset,T,Tc,Ca,qc,qc_cmd,T0,Tc_in,Ca0
90,7998.0000,fouling,0.2079,7988.8993,399.8411,359.3174,517.7649,85.5017,88.2507,299.3775,292.3299,2465.2718
T = 399.8411
Tc = 359.3174
qc = 85.5017
qc_cmd = 88.2507


#TEST - START
run_id,    time,       fault_kind,   severity,      onset       
98,         9292,       fouling,     0.3166,     9291.9106,
T,             Tc,         Ca,         qc,         qc_cmd,            
399.9926,   353.3900,   529.1633,  111.0864,       113.9476,    
T0,             Tc_in,              Ca0
301.2967,        293.0029,           2479.8100

#TEST - END
run_id,    time,       fault_kind,   severity,       onset       
98,         20160,       fouling,     0.3166,      9291.9106,
T,             Tc,         Ca,         qc,           qc_cmd,            
399.5487,   329.3996,   536.5154,    182.8588,       184.3933,    
T0,             Tc_in,              Ca0
301.1564,        293.1048,           2509.3330,

#TRUTH - START
run_id,    time,        fault_kind,   severity,      onset       
98,        9292,           fouling,     0.3166,     9291.9106,
T_true,             Tc_true,         Ca_true,        T0,             
400.1267,            352.8575,       525.4887,    2492.5779,          
Tc_in,                 Ca0,             UA_true,
300.7063,           293.2781,         599996.0688

#TRUTH - END
run_id,     time,       T_true,         Tc_true,        Ca_true,       
98,         20160,    399.1634,       329.6993,       539.2157,      
Ca0_true,       T0_true,        Tc_in_true,     UA_true
2489.1446,      301.0404,       292.8080,       410049.3071
