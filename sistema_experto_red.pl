% =========================================================================
% Proyecto: Centro de Operaciones de Seguridad · SOC (Sistema Experto de Producción & Búsqueda BFS)
% Autor: Angel Gabriel Castillo Castillo
% Copyright (c) 2026. Todos los derechos reservados. Licencia propietaria (ver archivo LICENSE).
% =========================================================================

% =========================================================================
% INSTITUTO TECNOLÓGICO SUPERIOR DE XALAPA (ITSX)
% ASIGNATURA: Inteligencia Artificial (SCC-1012)
% PROYECTO UNIDAD 2: Sistema Experto Basado en Redes Bayesianas
% DOMINIO: Diagnóstico de Fallas de Red en Laboratorio de Sistemas (6 Salones)
% =========================================================================

% -------------------------------------------------------------------------
% 1. PROBABILIDADES A PRIORI Y TABLAS DE PROBABILIDAD CONDICIONAL (CPT)
% Estados booleanos: true = Falla / Sin servicio, false = Operativo / Normal
% -------------------------------------------------------------------------

% Nodo Raíz: RedTelmex (Caída general del ISP Telmex: 4% de probabilidad a priori)
prob(red_telmex, true, 0.04).
prob(red_telmex, false, 0.96).

% CPT RouterCisco dado RedTelmex: P(RouterCisco | RedTelmex)
% Si Telmex falla (true), el router pierde salida (1.0).
% Si Telmex está OK (false), el router tiene 2% de probabilidad de falla propia.
cpt_router(true, true, 1.00).
cpt_router(false, true, 0.00).
cpt_router(true, false, 0.02).
cpt_router(false, false, 0.98).

% CPT SwitchDist (Switch Gigabit central) dado RouterCisco: P(SwitchDist | RouterCisco)
% Si el Router falla, el SwitchDist pierde conexión (1.0).
% Si el Router está OK, el SwitchDist tiene 3% de probabilidad de falla propia.
cpt_sw_dist(true, true, 1.00).
cpt_sw_dist(false, true, 0.00).
cpt_sw_dist(true, false, 0.03).
cpt_sw_dist(false, false, 0.97).

% CPT Switch2960_S1 (Salón 1) dado SwitchDist: P(Switch2960_S1 | SwitchDist)
% Si SwitchDist falla, el Switch del Salón 1 pierde red (1.0).
% Si SwitchDist está OK, el Switch 2960 del Salón 1 tiene 5% de falla propia.
cpt_sw_s1(true, true, 1.00).
cpt_sw_s1(false, true, 0.00).
cpt_sw_s1(true, false, 0.05).
cpt_sw_s1(false, false, 0.95).

% CPT Switch2960_S2 (Salón 2 - Testigo) dado SwitchDist: P(Switch2960_S2 | SwitchDist)
% Condicionalmente independiente de Switch2960_S1 dado SwitchDist.
cpt_sw_s2(true, true, 1.00).
cpt_sw_s2(false, true, 0.00).
cpt_sw_s2(true, false, 0.05).
cpt_sw_s2(false, false, 0.95).

% CPT PC_S1_E1 (Equipo 1 del Salón 1) dado Switch2960_S1: P(PC_S1_E1 | Switch2960_S1)
% Cumple restricción de la práctica: P(PC_S1_E1=falla | Switch2960_S1=falla) = 1.0
% Si el switch está OK, la PC tiene 8% de probabilidad de fallo físico aislado (cable/NIC).
cpt_pc_s1_e1(true, true, 1.00).
cpt_pc_s1_e1(false, true, 0.00).
cpt_pc_s1_e1(true, false, 0.08).
cpt_pc_s1_e1(false, false, 0.92).

% CPT PC_S1_Resto (Resto de las 23 PCs del Salón 1) dado Switch2960_S1
% Que todas las demás PCs fallen al mismo tiempo por daño aislado si el switch sirve es 0.001.
cpt_pc_s1_resto(true, true, 1.00).
cpt_pc_s1_resto(false, true, 0.00).
cpt_pc_s1_resto(true, false, 0.001).
cpt_pc_s1_resto(false, false, 0.999).

% CPT PC_S2_E1 (Equipos del Salón 2) dado Switch2960_S2
cpt_pc_s2(true, true, 1.00).
cpt_pc_s2(false, true, 0.00).
cpt_pc_s2(true, false, 0.08).
cpt_pc_s2(false, false, 0.92).

% -------------------------------------------------------------------------
% 2. REGLA DE LA CADENA: PROBABILIDAD CONJUNTA GLOBAL
% P(T, R, SD, S1, S2, PC1, PCR, PC2) = P(T)*P(R|T)*P(SD|R)*P(S1|SD)*P(S2|SD)*P(PC1|S1)*P(PCR|S1)*P(PC2|S2)
% -------------------------------------------------------------------------

prob_conjunta(T, R, SD, S1, S2, PC1, PCR, PC2, ProbTotal) :-
    prob(red_telmex, T, PT),
    cpt_router(R, T, PR),
    cpt_sw_dist(SD, R, PSD),
    cpt_sw_s1(S1, SD, PS1),
    cpt_sw_s2(S2, SD, PS2),
    cpt_pc_s1_e1(PC1, S1, PPC1),
    cpt_pc_s1_resto(PCR, S1, PPCR),
    cpt_pc_s2(PC2, S2, PPC2),
    ProbTotal is PT * PR * PSD * PS1 * PS2 * PPC1 * PPCR * PPC2.

% -------------------------------------------------------------------------
% 3. INFERENCIA BAYESIANA: P(Causa | Evidencia) = P(Causa, Evidencia) / P(Evidencia)
% -------------------------------------------------------------------------

% Calcula la probabilidad marginal de la evidencia observada P(E)
prob_evidencia(PC1, PCR, PC2, ProbE) :-
    findall(P, prob_conjunta(_, _, _, _, _, PC1, PCR, PC2, P), Lista),
    sum_list(Lista, ProbE).

% Identificación de probabilidad posterior de falla activa en cada nodo
prob_nodo_falla(red_telmex, PC1, PCR, PC2, ProbPosterior) :-
    prob_evidencia(PC1, PCR, PC2, ProbE), ProbE > 0,
    findall(P, prob_conjunta(true, _, _, _, _, PC1, PCR, PC2, P), L),
    sum_list(L, PConj), ProbPosterior is PConj / ProbE.

prob_nodo_falla(router_cisco, PC1, PCR, PC2, ProbPosterior) :-
    prob_evidencia(PC1, PCR, PC2, ProbE), ProbE > 0,
    findall(P, prob_conjunta(false, true, _, _, _, PC1, PCR, PC2, P), L),
    sum_list(L, PConj), ProbPosterior is PConj / ProbE.

prob_nodo_falla(switch_dist, PC1, PCR, PC2, ProbPosterior) :-
    prob_evidencia(PC1, PCR, PC2, ProbE), ProbE > 0,
    findall(P, prob_conjunta(false, false, true, _, _, PC1, PCR, PC2, P), L),
    sum_list(L, PConj), ProbPosterior is PConj / ProbE.

prob_nodo_falla(switch_2960_s1, PC1, PCR, PC2, ProbPosterior) :-
    prob_evidencia(PC1, PCR, PC2, ProbE), ProbE > 0,
    findall(P, prob_conjunta(false, false, false, true, _, PC1, PCR, PC2, P), L),
    sum_list(L, PConj), ProbPosterior is PConj / ProbE.

prob_nodo_falla(pc_s1_e1_aislada, PC1, PCR, PC2, ProbPosterior) :-
    prob_evidencia(PC1, PCR, PC2, ProbE), ProbE > 0,
    findall(P, prob_conjunta(false, false, false, false, _, PC1, PCR, PC2, P), L),
    sum_list(L, PConj), ProbPosterior is PConj / ProbE.

% Regla solicitada en la práctica: diagnostico_falla/2
% Recibe Evidencia = [PC_S1_E1, Resto_Salon1, Salon2] y devuelve lista de probabilidades de causa raíz
diagnostico_falla([PC1, PCR, PC2], Resultados) :-
    prob_nodo_falla(red_telmex, PC1, PCR, PC2, PTelmex),
    prob_nodo_falla(router_cisco, PC1, PCR, PC2, PRouter),
    prob_nodo_falla(switch_dist, PC1, PCR, PC2, PSwDist),
    prob_nodo_falla(switch_2960_s1, PC1, PCR, PC2, PSwS1),
    prob_nodo_falla(pc_s1_e1_aislada, PC1, PCR, PC2, PPC1),
    Resultados = [
        causa(red_telmex, PTelmex),
        causa(router_cisco, PRouter),
        causa(switch_dist, PSwDist),
        causa(switch_2960_s1, PSwS1),
        causa(pc_s1_e1_aislada, PPC1)
    ].

% Predicado auxiliar para exportar datos limpios hacia la interfaz gráfica en Python
consulta_gui(PC1, PCR, PC2) :-
    prob_evidencia(PC1, PCR, PC2, PE),
    prob_nodo_falla(red_telmex, PC1, PCR, PC2, PT),
    prob_nodo_falla(router_cisco, PC1, PCR, PC2, PR),
    prob_nodo_falla(switch_dist, PC1, PCR, PC2, PSD),
    prob_nodo_falla(switch_2960_s1, PC1, PCR, PC2, PS1),
    prob_nodo_falla(pc_s1_e1_aislada, PC1, PCR, PC2, PPC),
    format('RESULTADO|~6f|~6f|~6f|~6f|~6f|~6f~n', [PE, PT, PR, PSD, PS1, PPC]).