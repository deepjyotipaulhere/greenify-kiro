import { Collapsible } from '@/components/Collapsible';
import ProgressSteps, { Content } from '@joaosousa/react-native-progress-steps';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Button, Card, Layout, Text, useTheme } from '@ui-kitten/components';
import { useCameraPermissions } from 'expo-camera';
import { Image } from 'expo-image';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import { useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, useWindowDimensions } from 'react-native';

type Answer = {
	description: string
	plants: [
		{
			name: string
			AR_model: string
			care_instructions: string
			care_tips: string
			description: string
			image: string
		}
	]
}

export default function Home() {
	const [permission, requestPermission] = useCameraPermissions();
	const theme = useTheme()
	const { width } = useWindowDimensions()
	const router = useRouter()

	const [step, setStep] = useState(0);
	const [cameraPermission, setCameraPermission] = useState(false)
	const [locationPermission, setLocationPermission] = useState(false)
	const [plants, setPlants] = useState<null | Answer>(null)
	const [loading, setLoading] = useState(false)

	const [cameraImage, setCameraImage] = useState<string | null>(null)
	const [location, setLocation] = useState<null | [number, number, number]>(null)
	const [communityShare, setCommunityShare] = useState(false)

	useEffect(() => {
		AsyncStorage.clear()
	}, [])


	const step2 = () => {
		// Allow permissions

		// if (!permission?.granted) {
		// 	requestPermission().then((perm) => {
		// 		if (perm.status === 'granted')
		// 			setCameraPermission(true)
		// 	})
		// }

		if (Location.PermissionStatus.DENIED) {
			Location.requestForegroundPermissionsAsync().then((perm) => {
				if (perm.status === 'granted')
					setLocationPermission(true)
			})
		}

		// if (Location.PermissionStatus.GRANTED === 'granted')
		setStep(step + 1)
	}

	const step3 = () => {
		const openCamera = async () => {
			const camera = await ImagePicker.launchCameraAsync({
				mediaTypes: ImagePicker.MediaTypeOptions.Images,
				quality: 1,
				base64: true
			});
			if (!camera.canceled) {
				setCameraImage(`data:image/jpeg;base64,${camera.assets[0]?.base64}`);
				setStep(step + 1);
			}
		};
		const captureLocation = async () => {
			const { coords } = await Location.getCurrentPositionAsync({});
			console.log(coords);

			setLocation([coords.latitude, coords.longitude, coords.altitude ?? 0]);
		};

		captureLocation();
		openCamera();

	}

	// useEffect(() => {
	// 	if (cameraImage && location) {
	// 		console.log(cameraImage.substring(0, 50));
	// 		console.log(location);
	// 		setStep(step + 1);
	// 	}
	// }, [cameraImage, location])


	const step4 = () => {
		setLoading(true)
		setTimeout(() => {

			// fetch("https://greenify-service-g0fre7fva8fxcmhs.centralindia-01.azurewebsites.net/answer", {
				fetch("http://192.168.0.100:5000/answer", {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Accept': 'application/json',
				},
				body: JSON.stringify({
					image: cameraImage,
					location
				})
			}).then(response => response.json()).then(data => {
				console.log(data);

				setPlants(data)
				setLoading(false)
				setStep(step + 1)
			}).catch(err => {
				console.log(err.response);
			}).finally(() => {
				setLoading(false)
			})
		}, 1000);
	}

	const step6 = () => {
		AsyncStorage.setItem(
			'user',
			JSON.stringify([{ name: 'User', plants: plants?.plants.map(p => p.name) }])).then(() => {
				setStep(step + 1)
				router.navigate("/(tabs)/community")
			})
	}

	return (
		<Layout style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
			<ScrollView style={{ width: '100%' }}>
				<ProgressSteps
					currentStep={step}
					steps={[
						{
							id: 1,
							title: <Text category='h6' style={{ fontFamily: 'Borel', color: theme['color-primary-default'] }}>Welcome</Text>,
							content: <Content>
								<Text category='h6' style={{ fontFamily: 'Roboto', marginBottom: 10 }}>Greenify helps turn any space into a living, breathing ecosystem with the help of AI</Text>
								<Button onPress={() => setStep(step + 1)} size='small'>Get Started</Button>
							</Content>,
						},
						{
							id: 2,
							title: <Text category='h6' style={{ fontFamily: 'Borel', color: theme['color-primary-default'] }}>What we need</Text>,
							content: <Content>
								<Text category='h6' style={{ fontFamily: 'Roboto', marginBottom: 10 }}>We only need a photo of the place you want to plant trees and your location. The place can be a street corner, an open space, your backyard or a balcony</Text>
								<Button onPress={step2} size='small'>{(cameraPermission && locationPermission) ? "Proceed" : "Allow Camera and Location"}</Button>
							</Content>,
						},
						{
							id: 3,
							title: <Text category='h6' style={{ fontFamily: 'Borel', color: theme['color-primary-default'] }}>Capture Photo</Text>,
							content: <Content>
								<Text category='h6' style={{ fontFamily: 'Roboto', marginBottom: 10 }}>Capture a photo of the place you want to Greenify</Text>
								<Button onPress={step3} size='small'>Take Photo</Button>
							</Content>,
						},
						{
							id: 4,
							title: <Text category='h6' style={{ fontFamily: 'Borel', color: theme['color-primary-default'] }}>Confirm Data</Text>,
							content: <Content>
								{
									cameraImage ? (
										// <View style={styles.container}>
										<Image source={{ uri: cameraImage }} style={{ height: 200, width: 200 }} contentFit="cover" />
										// </View>
									) : (
										<Text category='h6' style={{ fontFamily: 'Roboto', marginBottom: 10 }}>No image captured yet.</Text>
									)}
								<Button onPress={step4} size='small' style={{ marginTop: 10, width: 300 }}>Start Greenify</Button>
								{loading ? <Text>Loading...</Text> : <></>}
							</Content>
						},
						{
							id: 5,
							title: <Text category='h6' style={{ fontFamily: 'Borel', color: theme['color-primary-default'] }}>Greenifications</Text>,
							content: <Content>
								<>
									<Text category='h6' style={{ fontFamily: 'Roboto', marginBottom: 10 }}>{plants?.description}</Text>
									<ScrollView horizontal>
										{
											plants?.plants.map(plant =>
												<Card key={plant.name} style={{ marginRight: 20, width: width * 0.6 }}
													header={<Text category='h4' style={{ fontFamily: 'Borel', color: theme['color-primary-default'] }}>{plant.name}</Text>}
												>
													<Text>
														{plant.description}
													</Text>
													<Collapsible title='Plant care tips'>
														{plant.care_instructions}
													</Collapsible>
												</Card>)
										}
									</ScrollView>
								</>
								<Button onPress={() => setStep(step + 1)} size='small'>Perfect</Button>
							</Content>,
						},
						{
							id: 6,
							title: <Text category='h6' style={{ fontFamily: 'Borel', color: theme['color-primary-default'] }}>Share with Community</Text>,
							content: <Content>
								<Text category='h6' style={{ fontFamily: 'Roboto', marginBottom: 10 }}>Sharing with community allows you to get help from friends, neighbours, locals, environmental activists and NGOs. You can get help greenifying the place from them which can make the process faster and creates happiness in a collective way</Text>
								<Button onPress={step6} size='small'>Go to Community</Button>
							</Content>
						}
					]}
					colors={{
						title: {
							text: {
								normal: '#94d2bd',
								active: '#fc0',
								completed: theme['color-primary-default'],
							}
						},
						marker: {
							text: {
								normal: '#94d2bd',
								active: theme['color-primary-default'],
								completed: '#fc0',
							},
							line: {
								normal: '#94d2bd',
								active: theme['color-primary-default'],
								completed: '#fc0',
							},
						},
					}}
				/>
			</ScrollView>
		</Layout >
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: '#fff',
		alignItems: 'center',
		justifyContent: 'center',
	},
	image: {
		height: 200,
		width: 200,
		padding: 10,
		backgroundColor: '#0553',
	},
});