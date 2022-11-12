{% load static %}

const clickSound = new Audio()
clickSound.src = "{% static 'audios/button_click.mp3' %}"



//háttér mozgás
function moveBackgroundOnMouseMovement(backgroundImageID, containerID){
	const pageBackground = document.querySelector(backgroundImageID)
	const containerBackground = document.querySelector(containerID) //registration-page-content lefedi az egesz kepes backgroundot, ezert azon kell erzekelni a mousemove-ot

	const windowWidth = window.innerWidth


	$(containerBackground).mousemove(function(event){
		var moveDirX = event.clientX / (windowWidth / 2)

		pageBackground.style.transform = `translate3d(-${moveDirX}%, 0, 0)`
	})
}