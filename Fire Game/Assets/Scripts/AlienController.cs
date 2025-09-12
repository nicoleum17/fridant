using System.Collections.Generic;
using UnityEngine;

public class AlienController : MonoBehaviour
{
    public GameObject alienShipPrefab;
    public GameObject alienSquadPrefab;
    public GameObject victimPrefab;
    public GameObject POIPrefab;

    private List<GameObject> activeShips = new List<GameObject>();
    private List<GameObject> activeSquads = new List<GameObject>();
    private List<GameObject> activeVictims = new List<GameObject>();
    private List<GameObject> activePOI = new List<GameObject>();
    private void OnEnable()
    {
        GameManager.OnStateChanged += HandleSimulationUpdate;
    }

    private void OnDisable()
    {
        GameManager.OnStateChanged -= HandleSimulationUpdate;
    }

    private void HandleSimulationUpdate(SimulationState state)
    {
        foreach (GameObject shipObject in activeShips)
        {
            Destroy(shipObject);
        }
        activeShips.Clear();
        foreach (GameObject squadObject in activeSquads)
        {
            Destroy(squadObject);
        }
        activeVictims.Clear();
        foreach (GameObject victimObject in activeVictims)
        {
            Destroy(victimObject);
        }
        activeSquads.Clear();
        foreach (GameObject POIObject in activePOI)
        {
            Destroy(POIObject);
        }
        activePOI.Clear();

        if (state.model_data.matriz == null) return;

        for (int i = 0; i < (state.model_data.matriz.Count); i++)
        {
            int x = i / state.model_data.height;
            int y = i % state.model_data.height;

            int cellValue = state.model_data.matriz[i];
            if (cellValue == 5 || cellValue == 6)
            {
                Vector3 position = new Vector3(state.cuadriculaVictima[x, y, 0], 0.31f, state.cuadriculaVictima[x, y, 1]);

                GameObject newVictim = Instantiate(victimPrefab, position, Quaternion.identity);

                activeVictims.Add(newVictim);
            }
            if (cellValue == 1 || cellValue == 2)
            {
                Vector3 position = new Vector3(state.cuadricula[x, y, 0], 0.31f, state.cuadricula[x, y, 1]);

                GameObject newPOI = Instantiate(POIPrefab, position, Quaternion.identity);

                activePOI.Add(newPOI);
            }

            if (cellValue == 2 || cellValue == 3 || cellValue == 6)
            {
                Vector3 position = new Vector3(state.cuadriculaHole[x, y, 0], 0.31f, state.cuadriculaHole[x, y, 1]);

                GameObject newShip = Instantiate(alienShipPrefab, position, Quaternion.identity);

                activeShips.Add(newShip);

                Debug.Log("Mi posicion original es:" + x + " " + y + "y en Unity es: " + state.cuadriculaVictima[x, y, 0] + state.cuadriculaVictima[x, y, 1]);
            }
            else if (cellValue == 4)
            {
                Vector3 position = new Vector3(state.cuadriculaAlien[x, y, 0], 0, state.cuadriculaAlien[x, y, 1]);

                GameObject newSquad = Instantiate(alienSquadPrefab, position, Quaternion.identity);

                activeSquads.Add(newSquad);
            }
        }
    }

}
