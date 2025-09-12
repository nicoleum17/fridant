using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

public class FlaskReciver : MonoBehaviour
{
    public Button nextStepButton;
    public Button newSimButton;
    void Start()
    {
        if (nextStepButton != null)
        {
            nextStepButton.onClick.AddListener(nextStep);
        }
        if (newSimButton != null) {
            newSimButton.onClick.AddListener(newSim);
        }


    }

    public void nextStep()
    {
        Debug.Log("Enviando siguiente step...");
        StartCoroutine(PostRequest("http://127.0.0.1:5000/new_step"));
    }

    public void newSim()
    {
        Debug.Log("Iniciando nueva sim...");
        StartCoroutine(PostRequest("http://127.0.0.1:5000/new_sim"));
    }


    IEnumerator PostRequest(string uri)
    {
        using (UnityWebRequest webRequest = new UnityWebRequest(uri, "POST"))
        {
            webRequest.downloadHandler = new DownloadHandlerBuffer();

            yield return webRequest.SendWebRequest();
            if (webRequest.result == UnityWebRequest.Result.ConnectionError || webRequest.result == UnityWebRequest.Result.ProtocolError)
            {
                Debug.Log("Error" + webRequest.error);
            }
            else
            {
                string jsonResponse = webRequest.downloadHandler.text;
                Debug.Log("Respuesta recibida: " + jsonResponse);

                SimulationState state = JsonUtility.FromJson<SimulationState>(jsonResponse);
                if (state != null)
                {
                    GameManager.Instance.UpdateSimulationState(state);
                }


            }
        }
    }
}
