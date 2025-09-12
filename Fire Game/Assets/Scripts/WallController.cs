using System.Collections.Generic;
using UnityEngine;

public class WallController : MonoBehaviour
{
    public GameObject DoorsPrefab;
    public GameObject WallPrefab;
    private List<GameObject> activeDoors = new List<GameObject>();
    private List<GameObject> activeWalls = new List<GameObject>();
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
        int r = 0;
        foreach (GameObject doorObject in activeDoors)
        {
            Destroy(doorObject);
        }
        activeDoors.Clear();
        foreach (GameObject wallObject in activeWalls)
        {
            Destroy(wallObject);
        }
        activeWalls.Clear();
        if (state.model_data.matriz_muros == null) return;
        for (int i = 0; i < (state.model_data.matriz_muros.Count); i++)
        {
            int z = i % 4-1;
            if (z == -1) {
                z = 3;
            }
            int y = (i / 4) % (state.model_data.height);
            int x = (i) / (state.model_data.height * 4);
            int cellValue = state.model_data.matriz_muros[i];

            if (i % 2 != 0) {
                r = 0;
            }
            else
            {
                r = 90;
            }
            if (cellValue == 3)
            {

                Vector3 position = new Vector3(state.cuadriculaPuertasPared[x, y, z, 0], 0.96f, state.cuadriculaPuertasPared[x, y, z, 1]);



                Quaternion rotation = Quaternion.Euler(90, 0, r);

                GameObject newDoor = Instantiate(DoorsPrefab, position, rotation);

                activeDoors.Add(newDoor);


            }
            else if (cellValue == 2) {
                Vector3 position = new Vector3(state.cuadriculaPuertasPared[x, y, z, 0], 0.96f, state.cuadriculaPuertasPared[x, y, z, 1]);



                Quaternion rotation = Quaternion.Euler(90, 0, r);

                GameObject newWall = Instantiate(WallPrefab, position, rotation);

                activeWalls.Add(newWall);

            }



        }
    }
}
