import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Button, Card, Divider, Layout, ListItem, Text, useTheme } from '@ui-kitten/components';
import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, useWindowDimensions } from 'react-native';


interface User {
	name: string;
	plants: string[]
}

export default function TabTwoScreen() {
	const { width } = useWindowDimensions()
	const theme = useTheme()

	const [loading, setLoading] = useState(false)
	interface Match {
		users: string[];
		description: string[];
		benefits: [{
			amount: string;
			direction: boolean;
			type: string
		}]
	}

	const [matches, setMatches] = useState<Match[] | null>(null)

	const [users, setUsers] = useState<User[]>([])

	const getUser = async () => {
		// const res = await fetch("https://greenify-service-g0fre7fva8fxcmhs.centralindia-01.azurewebsites.net/users", {
		const res = await fetch("http://192.168.0.100:5000/users", {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				'Accept': 'application/json',
			},
		})
		const fUsers: [] = await res.json()
		const sUser: [] = JSON.parse(await AsyncStorage.getItem('user') || '[]')

		setUsers([...sUser, ...fUsers])
	}

	useEffect(() => {
		getUser()
	}, [])


	const startMatching = async () => {
		setLoading(true)
		const res = await fetch("https://greenify-service-g0fre7fva8fxcmhs.centralindia-01.azurewebsites.net/community", {
		// const res = await fetch("http://localhost:5000/community", {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Accept': 'application/json',
			},
			body: JSON.stringify({ users })
		})
		const data = await res.json()
		console.log(data);
		setMatches(data.match)
		setLoading(false)
	}

	return (
		<ScrollView>
			<Layout style={{ flex: 1 }}>
				<Layout style={{ flex: 1, height: 200, justifyContent: 'center', alignItems: 'center', backgroundColor: theme['color-primary-900'] }}>
					<Text category='h1' style={{ fontFamily: 'Borel' }}>Community</Text>
				</Layout>
				<Text category='h5' style={{ fontFamily: 'Borel', textAlign: 'center', marginTop: 20 }}>Users nearby</Text>
				<Divider />
				{users.map((user: User) => (
					<ListItem
						key={user.name}
						title={user.name}
						description={(props: any) => (
							<>
								<Text {...props} category="c2">willing to plant {user.plants.length} trees</Text>
								<ScrollView horizontal>
									{user.plants.map(plant => (
										<Layout
											key={plant}
											style={{
												padding: 5,
												margin: 5,
												borderRadius: 10,
												backgroundColor: theme['color-primary-100'],
											}}
										>
											<Text category="c1" style={{ color: theme['color-primary-600'] }}>
												{plant}
											</Text>
										</Layout>
									))}
								</ScrollView>
							</>
						)}
						accessoryLeft={(props: any) => (
							<Ionicons
								name="person-circle"
								size={50}
								color={theme['color-primary-default']}
							/>
						)}
					/>
				))}

			</Layout>
			{
				matches ? <>
					<Layout style={{ padding: 15, backgroundColor: theme['color-primary-900'] }}>
						<Text category='h5' style={{ fontFamily: 'Borel', textAlign: 'center' }}>New Community matches</Text>
						<Text category='s2' style={{ textAlign: 'center', marginBottom: 20 }}>powered by Perplexity AI</Text>
						{matches.map((match, index) => <Card key={match.users.join("")} style={{ marginBottom: 15 }} header={<>
							<Text style={{ textAlign: 'center', marginTop: 10 }}>Community {index + 1}</Text>
							<Text category='h4' style={{ textAlign: 'center', marginBottom: 10 }}>{match.users.join(", ")}</Text>
						</>}>
							<Text>{match.description}</Text>
							<ScrollView horizontal style={{ marginTop: 20 }}>
								{match.benefits.map((benefit, bindex) => <>
									<Layout
										key={bindex}
										style={{
											padding: 10,
											borderRadius: 10,
											marginRight: 10,
											backgroundColor: theme['color-info-200'],
										}}
									>
										<Text category='h3' style={{ textAlign: 'center', color: theme['color-info-900'] }}>{benefit.direction ? '↑' : '↓'} {benefit.amount}</Text>
										<Text category="s1" style={{ color: theme['color-info-800'] }}>
											{benefit.type}
										</Text>
									</Layout>

								</>)}
							</ScrollView>
						</Card>)}
					</Layout>
				</> : <Button style={{ margin: 15 }} onPress={startMatching}>Start Matching</Button>
			}
		</ScrollView >
	);
}

const styles = StyleSheet.create({
	headerImage: {
		color: '#808080',
		bottom: -90,
		left: -35,
		position: 'absolute',
	},
	titleContainer: {
		flexDirection: 'row',
		gap: 8,
	},
});
