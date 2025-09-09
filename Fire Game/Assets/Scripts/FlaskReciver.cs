using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

public class FlaskReciver : MonoBehaviour
{
    public Button nextStepButton;
    void Start()
    {
        if (nextStepButton != null)
        {
            nextStepButton.onClick.AddListener(nextStep);
        }
            
    }

    public void nextStep()
    {
        Debug.Log("Enviando siguiente step...");
        StartCoroutine(PostRequest("http://127.0.0.1:5000/new_step"));
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
